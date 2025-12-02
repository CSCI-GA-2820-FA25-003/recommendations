$(function () {
    const API_BASE_URL = "/recommendations";
    const VALID_REC_TYPES = ["cross-sell", "up-sell", "accessory"];
    const VALID_STATUSES = ["active", "inactive"];

    function trimmedValue(selector) {
        const value = $(selector).val();
        return typeof value === "string" ? value.trim() : "";
    }

    function setField(selector, value) {
        if (value === undefined || value === null) {
            $(selector).val("");
        } else {
            $(selector).val(value);
        }
    }

    function update_form_data(res) {
        if (!res) {
            return;
        }

        setField("#recommendation_id", res.recommendation_id);
        setField("#base_product_id", res.base_product_id);
        setField("#recommended_product_id", res.recommended_product_id);
        setField("#recommendation_type", res.recommendation_type);
        setField("#status", res.status);
        setField("#confidence_score", res.confidence_score);
        setField("#base_product_price", res.base_product_price);
        setField("#recommended_product_price", res.recommended_product_price);
        setField("#base_product_description", res.base_product_description);
        setField("#recommended_product_description", res.recommended_product_description);
        setField("#created_date", res.created_date);
        setField("#updated_date", res.updated_date);
    }

    function clear_form_data() {
        setField("#recommendation_id", "");
        setField("#base_product_id", "");
        setField("#recommended_product_id", "");
        setField("#recommendation_type", "");
        setField("#status", "");
        setField("#confidence_score", "");
        setField("#base_product_price", "");
        setField("#recommended_product_price", "");
        setField("#base_product_description", "");
        setField("#recommended_product_description", "");
        setField("#created_date", "");
        setField("#updated_date", "");
        $("#search_results").empty();
    }

    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").text(message);
    }

    function extract_error(res, fallback) {
        if (res && res.responseJSON && res.responseJSON.message) {
            return res.responseJSON.message;
        }
        if (res && res.responseText) {
            return res.responseText;
        }
        return fallback || "Server error";
    }

    function readIntegerField(selector, label, required) {
        const value = trimmedValue(selector);
        if (!value) {
            return required ? { error: label + " is required" } : { value: null };
        }
        const number = parseInt(value, 10);
        if (Number.isNaN(number)) {
            return { error: label + " must be an integer" };
        }
        return { value: number };
    }

    function readDecimalField(selector, label) {
        const value = trimmedValue(selector);
        if (!value) {
            return { value: undefined };
        }
        const number = Number(value);
        if (Number.isNaN(number)) {
            return { error: label + " must be a number" };
        }
        return { value: number };
    }

    function readConfidenceScore(required) {
        const value = trimmedValue("#confidence_score");
        if (!value) {
            return required ? { error: "Confidence Score is required" } : { value: undefined };
        }
        const number = Number(value);
        if (Number.isNaN(number) || number < 0 || number > 1) {
            return { error: "Confidence Score must be a number between 0 and 1" };
        }
        return { value: Number(number.toFixed(2)) };
    }

    function buildCreatePayload() {
        const baseId = readIntegerField("#base_product_id", "Base Product ID", true);
        if (baseId.error) {
            return baseId;
        }

        const recommendedId = readIntegerField("#recommended_product_id", "Recommended Product ID", true);
        if (recommendedId.error) {
            return recommendedId;
        }

        const typeRaw = trimmedValue("#recommendation_type");
        const type = typeRaw ? typeRaw.toLowerCase() : "";
        if (!type) {
            return { error: "Recommendation Type is required" };
        }
        if (VALID_REC_TYPES.indexOf(type) === -1) {
            return { error: "Recommendation Type must be one of: " + VALID_REC_TYPES.join(", ") };
        }

        const statusRaw = trimmedValue("#status");
        const status = (statusRaw ? statusRaw.toLowerCase() : "") || "active";
        if (VALID_STATUSES.indexOf(status) === -1) {
            return { error: "Status must be one of: " + VALID_STATUSES.join(", ") };
        }

        const confidence = readConfidenceScore(true);
        if (confidence.error) {
            return confidence;
        }

        const payload = {
            base_product_id: baseId.value,
            recommended_product_id: recommendedId.value,
            recommendation_type: type,
            status: status,
            confidence_score: confidence.value,
        };

        const basePrice = readDecimalField("#base_product_price", "Base Product Price");
        if (basePrice.error) {
            return basePrice;
        }
        if (basePrice.value !== undefined) {
            payload.base_product_price = basePrice.value;
        }

        const recPrice = readDecimalField("#recommended_product_price", "Recommended Product Price");
        if (recPrice.error) {
            return recPrice;
        }
        if (recPrice.value !== undefined) {
            payload.recommended_product_price = recPrice.value;
        }

        const baseDescription = trimmedValue("#base_product_description");
        if (baseDescription) {
            payload.base_product_description = baseDescription;
        }

        const recDescription = trimmedValue("#recommended_product_description");
        if (recDescription) {
            payload.recommended_product_description = recDescription;
        }

        return { value: payload };
    }

    function escapeHtml(value) {
        if (value === undefined || value === null) {
            return "";
        }
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatNumber(value) {
        if (value === undefined || value === null || value === "") {
            return "";
        }
        const number = Number(value);
        if (Number.isNaN(number)) {
            return value;
        }
        return number.toFixed(2);
    }

    function renderResultsTable(items) {
        const list = Array.isArray(items) ? items : [items];
        if (!list.length) {
            $("#search_results").empty();
            $("#search_results").append("<p>No recommendations found.</p>");
            return;
        }

        let table = '<table class="table table-striped" cellpadding="10">';
        table += "<thead><tr>";
        table += '<th class="col-md-1">ID</th>';
        table += '<th class="col-md-2">Base Product ID</th>';
        table += '<th class="col-md-2">Recommended Product ID</th>';
        table += '<th class="col-md-2">Type</th>';
        table += '<th class="col-md-1">Status</th>';
        table += '<th class="col-md-1">Confidence</th>';
        table += '<th class="col-md-1">Base Price</th>';
        table += '<th class="col-md-1">Recommended Price</th>';
        table += '<th class="col-md-3">Base Description</th>';
        table += '<th class="col-md-3">Recommended Description</th>';
        table += '<th class="col-md-2">Created</th>';
        table += '<th class="col-md-2">Updated</th>';
        table += "</tr></thead><tbody>";

        list.forEach(function (item, index) {
            table += '<tr id="row_' + index + '">';
            table += "<td>" + escapeHtml(item.recommendation_id) + "</td>";
            table += "<td>" + escapeHtml(item.base_product_id) + "</td>";
            table += "<td>" + escapeHtml(item.recommended_product_id) + "</td>";
            table += "<td>" + escapeHtml(item.recommendation_type) + "</td>";
            table += "<td>" + escapeHtml(item.status) + "</td>";
            table += "<td>" + escapeHtml(formatNumber(item.confidence_score)) + "</td>";
            table += "<td>" + escapeHtml(formatNumber(item.base_product_price)) + "</td>";
            table += "<td>" + escapeHtml(formatNumber(item.recommended_product_price)) + "</td>";
            table += "<td>" + escapeHtml(item.base_product_description) + "</td>";
            table += "<td>" + escapeHtml(item.recommended_product_description) + "</td>";
            table += "<td>" + escapeHtml(item.created_date) + "</td>";
            table += "<td>" + escapeHtml(item.updated_date) + "</td>";
            table += "</tr>";
        });

        table += "</tbody></table>";
        $("#search_results").empty();
        $("#search_results").append(table);
    }

    function handleAjaxFail(xhr, defaultMessage) {
        flash_message(extract_error(xhr, defaultMessage));
    }

    $("#create-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        const payloadResult = buildCreatePayload();
        if (payloadResult.error) {
            flash_message(payloadResult.error);
            return;
        }

        const ajax = $.ajax({
            type: "POST",
            url: API_BASE_URL,
            contentType: "application/json",
            data: JSON.stringify(payloadResult.value),
        });

        ajax.done(function (res) {
            update_form_data(res);
            flash_message("Recommendation created (ID " + res.recommendation_id + ")");
        });

        ajax.fail(function (res) {
            handleAjaxFail(res, "Unable to create recommendation");
        });
    });

    $("#update-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        const idResult = readIntegerField("#recommendation_id", "Recommendation ID", true);
        if (idResult.error) {
            flash_message(idResult.error);
            return;
        }

        const payload = {};
        const typeValueRaw = trimmedValue("#recommendation_type");
        const typeValue = typeValueRaw ? typeValueRaw.toLowerCase() : "";
        if (typeValue) {
            if (VALID_REC_TYPES.indexOf(typeValue) === -1) {
                flash_message("Recommendation Type must be one of: " + VALID_REC_TYPES.join(", "));
                return;
            }
            payload.recommendation_type = typeValue;
        }

        const statusRaw = trimmedValue("#status");
        const statusValue = statusRaw ? statusRaw.toLowerCase() : "";
        if (statusValue) {
            if (VALID_STATUSES.indexOf(statusValue) === -1) {
                flash_message("Status must be one of: " + VALID_STATUSES.join(", "));
                return;
            }
            payload.status = statusValue;
        }

        const confidence = readConfidenceScore(false);
        if (confidence.error) {
            flash_message(confidence.error);
            return;
        }
        if (confidence.value !== undefined) {
            payload.confidence_score = confidence.value;
        }

        if (Object.keys(payload).length === 0) {
            flash_message("Provide at least one editable field (type, status, confidence score)");
            return;
        }

        const ajax = $.ajax({
            type: "PUT",
            url: API_BASE_URL + "/" + idResult.value,
            contentType: "application/json",
            data: JSON.stringify(payload),
        });

        ajax.done(function (res) {
            update_form_data(res);
            flash_message("Recommendation updated");
        });

        ajax.fail(function (res) {
            handleAjaxFail(res, "Unable to update recommendation");
        });
    });

    $("#retrieve-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        const idResult = readIntegerField("#recommendation_id", "Recommendation ID", true);
        if (idResult.error) {
            flash_message(idResult.error);
            return;
        }

        const ajax = $.ajax({
            type: "GET",
            url: API_BASE_URL + "/" + idResult.value,
            contentType: "application/json",
        });

        ajax.done(function (res) {
            update_form_data(res);
            flash_message("Success");
        });

        ajax.fail(function (res) {
            clear_form_data();
            handleAjaxFail(res, "Recommendation not found");
        });
    });

    $("#delete-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        const idResult = readIntegerField("#recommendation_id", "Recommendation ID", true);
        if (idResult.error) {
            flash_message(idResult.error);
            return;
        }

        const ajax = $.ajax({
            type: "DELETE",
            url: API_BASE_URL + "/" + idResult.value,
            contentType: "application/json",
        });

        ajax.done(function () {
            clear_form_data();
            flash_message("Recommendation deleted");
        });

        ajax.fail(function (res) {
            handleAjaxFail(res, "Server error while deleting recommendation");
        });
    });

    $("#clear-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();
        clear_form_data();
    });

        // ---- Search button: query by filters / or query all ----
    $("#query-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        const baseId = readIntegerField(
            "#base_product_id",
            "Base Product ID",
            false 
        );
        if (baseId.error) {
            flash_message(baseId.error);
            return;
        }

        const confidence = readConfidenceScore(false); 
        if (confidence.error) {
            flash_message(confidence.error);
            return;
        }

        // recommendation_type / status
        const typeRaw = trimmedValue("#recommendation_type");
        const type = typeRaw ? typeRaw.toLowerCase() : "";

        const statusRaw = trimmedValue("#status");
        const status = statusRaw ? statusRaw.toLowerCase() : "";

        // query string
        const params = [];

        if (baseId.value !== null) {
            params.push(
                "base_product_id=" + encodeURIComponent(baseId.value)
            );
        }

        if (type) {
            params.push(
                "recommendation_type=" + encodeURIComponent(type)
            );
        }

        if (status) {
            params.push("status=" + encodeURIComponent(status));
        }

        if (confidence.value !== undefined) {
            params.push(
                "confidence_score=" + encodeURIComponent(confidence.value)
            );
        }

        let url = API_BASE_URL;
        if (params.length > 0) {
            // filter -> /recommendations?...
            url = API_BASE_URL + "?" + params.join("&");
        }
        // emty params  →  GET /recommendations （query all）

        const ajax = $.ajax({
            type: "GET",
            url: url,
            contentType: "application/json",
        });

        ajax.done(function (res) {
            renderResultsTable(res);
            flash_message("Success");
        });

        ajax.fail(function (res) {
            $("#search_results").empty();
            clear_form_data();
            handleAjaxFail(res, "No recommendations found");
        });
    });

    // ---- List all recommendations  ----
    $("#list-btn").click(function (event) {
        event.preventDefault();
        $("#flash_message").empty();

        // clear filter
        setField("#base_product_id", "");
        setField("#recommendation_type", "");
        setField("#status", "");
        setField("#confidence_score", "");

        // Search click → query all
        $("#query-btn").click();
    });


    // // === List all recommendations ===
    // $("#list-btn").click(function (event) {
    //     event.preventDefault();
    //     $("#flash_message").empty();

    //     const ajax = $.ajax({
    //         type: "GET",
    //         url: API_BASE_URL,          // GET /recommendations (no filters)
    //         contentType: "application/json",
    //     });

    //     ajax.done(function (res) {
    //         renderResultsTable(res);    
    //         flash_message("Success");
    //     });

    //     ajax.fail(function (res) {
    //         $("#search_results").empty();
    //         handleAjaxFail(res, "Unable to list recommendations");
    //     });
    // });
});
