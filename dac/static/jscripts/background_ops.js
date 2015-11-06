
var poll_period = 1000;
var timeout_duration = 0.05;

var start_all_update_message_text = "Update devices and profiles lists..";
var complete_all_update_message_text = "Complete update devices and profiles lists";
var error_all_update_message_text = "Error update devices and profiles lists. Probably are connecting to Apple site problems";

var start_all_update_parameters =
{
    "start_task_request_parameters" :
    {
        "url" : "/browser/startallupdate/",
        "content_type" : "application/json; charset=utf-8",
        "data" : "",
        "request_type" : "POST"
    },

    "check_task_progress_request_parameters" :
    {
        "url" : "/browser/allupdateprogress/"
    }
};

console.log("background_ops.js load");

var server_error_message_tag = "#server_error_message";


var ajax_error_processor =  function(jqXHR, statusText, thrownError)
{
    if (jqXHR.status === 0)
    {
        $(server_error_message_tag).text("Error. Server not online.");
    }
    else if (jqXHR.status == 404)
    {
        $(server_error_message_tag).text("Error. Requested page not found.");
    }
    else if (jqXHR.status == 500)
    {
        $(server_error_message_tag).text("Internal Server Error.");
    }
    else if (statusText === 'parsererror')
    {
        $(server_error_message_tag).text("Error. Requested JSON parse failed.");
    }
    else if (statusText === 'timeout')
    {
        $(server_error_message_tag).text("Error. Server time out.");
    }
    else if (statusText === 'abort')
    {
        $(server_error_message_tag).text("Error. Ajax request aborted.");
    }
    else
    {
        $(server_error_message_tag).text("Uncaught Error. " + jqXHR.responseText);
    }
}

var generate_after_finish_all_update_function = function(per_page, current_page, all_update_message_tag_id, complete_all_update_message_text, error_all_update_message_text)
{

    return function(result)
    {
        var result_value = result.result_value;
        var retrieved_devices_count = parseInt(result_value["retrieved_devices_count"]);
        var retrieved_profiles_count = parseInt(result_value["retrieved_profiles_count"]);
        if (retrieved_devices_count == -1 && retrieved_profiles_count == -1)
        {
            $(all_update_message_tag_id).text(error_all_update_message_text);
        }
        else
        {
            $(all_update_message_tag_id).text(complete_all_update_message_text);
            reload_devices_list(per_page, current_page, "/browser/getdeviceslist/");
        }
    }
}

var reload_devices_list = function(records_per_page, current_page, items_view_url)
{
    if (current_page != undefined)
    {
        get_item_list("#devicelist", "#pagination", items_view_url, {"per_page" : records_per_page, "page_num" : current_page});
    }
}

function AsyncTaskProcessor(parameters_associative_array, before_start_task_action, after_finish_task_action)
{
    console.log("Call AsyncTaskProcessor");
    var poll_period = 1000;
    var timeout_duration = 0.05;

    var start_task_request_parameters = parameters_associative_array["start_task_request_parameters"];
    var check_task_progress_request_parameters = parameters_associative_array["check_task_progress_request_parameters"];
    // var additional_parameters = parameters_associative_array["additional_parameters"];

    var cache = true;

    if (start_task_request_parameters["cache"] != undefined)
    {
        cache = start_task_request_parameters["cache"];
    }

    var process_data = true;

    if (start_task_request_parameters["process_data"] != undefined)
    {
        process_data = start_task_request_parameters["process_data"];
    }


    this.set_poll_period = function(new_poll_period)
    {
        if (new_poll_period != undefined && (typeof new_poll_period) == "number")
        {
            poll_period = new_poll_period;
        }
        else
        {
            console.log("Bad poll_period value");
        }
    };

    this.set_timeout_duration = function(new_timeout_duration)
    {
        if (new_timeout_duration != undefined && (typeof new_timeout_duration) == "number")
        {
            this.timeout_duration = timeout_duration;
        }
        else
        {
            console.log("Bad poll_period value");
        }
    }

    this.start_task = function()
    {
        console.log("Call start task");
        // if (before_start_task_action != undefined && before_start_task_action != null && (typeof before_start_task_action) == "function")
        if (before_start_task_action != undefined && before_start_task_action != null)
        {
            // before_start_task_action(additional_parameters);
            before_start_task_action();
        }

        $.ajax(
            {
                url: start_task_request_parameters["url"],
                contentType: start_task_request_parameters["content_type"],
                //mimeType: "application/json",
                data: start_task_request_parameters["data"],
                type: start_task_request_parameters["request_type"],
                cache: cache,
                processData: process_data,
                success: function(result)
                {
                    var task_id = result.task_id;
                    console.log("task id: " + task_id);
                    if (task_id != undefined && task_id != null && task_id != "")
                    {
                        check_task_progress(task_id);
                    }
                    else
                    {
                        console.log("Incorrect task id");
                    }
                },
                error: function(jqXHR, statusText, thrownError)
                {
                    ajax_error_processor(jqXHR, statusText, thrownError)
                }
            }
        );
    };

    var check_task_progress =  function(task_id)
    {
        var check_status = function()
        {
            console.log("AsyncTaskProcessor: call check_status");
            $.ajax(
                {
                    url: check_task_progress_request_parameters["url"],
                    contentType: "application/json; charset=utf-8",
                    data: task_id,
                    type: "POST",
                    success: function(result)
                    {
                        if (result.state == "notready")
                        {
                            console.log("task not ready");
                        }
                        else if (result.state == "ready")
                        {
                            clearInterval(interval_id);

                            // if (after_finish_task_action != undefined && after_finish_task_action != null && (typeof after_finish_task_action) == "function")
                            if (after_finish_task_action != undefined && after_finish_task_action != null)
                            {
                                after_finish_task_action(result);
                            }
                        }
                        /*else
                        {
                            clearInterval(interval_id);
                            $(show_message_tag_id).text(unknown_state_message_text)
                            console.log(unknown_state_message_text);
                        }*/
                    },
                    error: function(jqXHR, statusText, thrownError)
                    {
                        clearInterval(interval_id);
                        ajax_error_processor(jqXHR, statusText, thrownError)
                    }

                }
            );
        }
        setTimeout(check_status, timeout_duration);
        var interval_id = setInterval(check_status, poll_period);
    }
}

var get_item_list = function(item_list_tag_id, pagination_tag_id, items_view_url, query_data, method="GET")
{
    $.ajax(
        {
            url: items_view_url,
            contentType: "application/json; charset=utf-8",
            type: method,
            data: query_data,
            success: function(result)
            {
                var item_list = result.item_list;
                var pagination = result.pagination
                $(item_list_tag_id).html(item_list);
                $(pagination_tag_id).html(pagination);
            }
        }
    );
}

var get_object_id = function(object_text_tag_id, text_divider)
{
    var text_containing_object_id = $(object_text_tag_id).text();
    var text_divider_index = text_containing_object_id.indexOf(text_divider);
    var object_id = text_containing_object_id.substring(text_divider_index + 1).trim();
    return object_id;
}

var get_page_num = function(full_url_object)
{
    var host_url = $(location).attr("origin");
    var full_href_url = full_url_object + "";
    var page_url_part = full_href_url.substr(host_url.length + 1);
    return page_url_part;
}

