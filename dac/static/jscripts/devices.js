var show_message_tag_id = "#addmultipledevicesmessagetag";
var add_multiple_html_report_tag = "#addmultipledeviceshtmlreport";

var all_update_message_tag_id = show_message_tag_id;

var input_device_name_tag_id = "#name";
var input_device_udid_tag_id = "#udid";
var show_add_single_device_message_tag_id = "#addname";
var show_add_single_device_udid_tag_id = "#addudid";


var add_devices_success_state_mesage = 'success'; // Fake message, I don't know right message
var add_devices_error_state_message = 'error'; // Fake message, I don't know right message
var add_devices_fail_state_message = 'fail'; // Fake message, I don't know right message

var html_report_tag_id = "#addudid";

//var start_message_text = "Update devices and profiles lists..";
//var complete_message_text = "Complete update devices and profiles lists";
var devices_view_url = "/browser/getdeviceslist/";

var after_finish_add_single_device = function(add_device_result)
{
    var add_device_state_message = add_device_result.result_value;
    console.log("add_device_state_message: " + add_device_state_message);
    var result_html = add_device_result.result_html;
    if (add_device_state_message.indexOf(add_devices_success_state_mesage) != -1)
    {
        document.getElementById(input_device_name_tag_id.substring(1)).value = "";
        document.getElementById(input_device_udid_tag_id.substring(1)).value = "";
        $(show_add_single_device_message_tag_id).text("Success add device ");
        var current_page = $("#current_page").text();
        var per_page = $("option:selected").val();

        var after_finish_all_update = generate_after_finish_all_update_function(per_page, current_page, all_update_message_tag_id, complete_all_update_message_text, error_all_update_message_text)
        var all_update_async_task_processor = new AsyncTaskProcessor(start_all_update_parameters, before_start_all_update, after_finish_all_update);
        all_update_async_task_processor.start_task();

    }
    else
    {
        $(show_add_single_device_message_tag_id).text("Fail add device");
        //$(html_report_tag_id).html(result_html);
        $(add_multiple_html_report_tag).html(result_html);
    }
}

var before_start_add_multiple_devices = function()
{
    $(show_message_tag_id).text("Start adding devices...");
}

var after_finish_add_multiple_devices = function(add_multiple_devices_result)
{
    var  add_multiple_devices_state_message = add_multiple_devices_result.result_value;
    var result_html = add_multiple_devices_result.result_html;
    console.log("complete_add_multiple_devices, add_devices_list_state_message: " + add_multiple_devices_state_message);

    var add_multiple_devices_success_message = "success";
    var add_multiple_devices_fail_message = "fail";

    var per_page = $("#devicesperpage option:selected").val();
    var current_page = $("#current_page").text();

    if (add_multiple_devices_state_message.indexOf(add_multiple_devices_success_message) != -1)
    {
        $(show_message_tag_id).text("Devices added sucessfully. Start updating devices info...");
        var after_finish_all_update = generate_after_finish_all_update_function(per_page, current_page, all_update_message_tag_id, complete_all_update_message_text, error_all_update_message_text);

        var all_update_async_task_processor = new AsyncTaskProcessor(start_all_update_parameters, before_start_all_update, after_finish_all_update);
        all_update_async_task_processor.start_task();

    }
    else if (add_multiple_devices_state_message.indexOf(add_multiple_devices_fail_message) != -1)
    {
        $(show_message_tag_id).text("Invalid add devices state")
        $(add_multiple_html_report_tag).html(result_html);
    }
    else
    {
        $(show_message_tag_id).text("Error by adding devices: " + add_multiple_devices_state_message);
        //$(add_multiple_html_report_tag).html(result_html);
    }
}

var before_start_all_update = function(result)
{
    $(all_update_message_tag_id).text(start_all_update_message_text);
};

window.onload = function()
{
    var per_page = $("#devicesperpage option:selected").val();

    get_item_list("#devicelist", "#pagination", "/browser/getdeviceslist/", {"per_page" : per_page, "page_num" : 1});
}

$(document).on("click", ".page_link", function(event)
    {
        event.preventDefault();

        var per_page = $("#devicesperpage option:selected").val();
        var page_num = get_page_num(this);

        get_item_list("#devicelist", "#pagination", "/browser/getdeviceslist/", {"per_page" : per_page, "page_num" : page_num});

        $("#addname").text("");
        $("#addudid").text("");
    }
);

$(document).ready(
    function()
    {
        $("#adddeviceform").submit(
            function(event)
            {
                event.preventDefault();

                var device_name = $(input_device_name_tag_id).val();
                var device_udid = $(input_device_udid_tag_id).val();
                var start_add_single_device_parameters =
                {
                    "start_task_request_parameters" :
                    {
                        "url" : "/browser/startadddevice/",
                        "content_type" : "application/x-www-form-urlencoded",
                        "data" : $("#adddeviceform").serialize(),
                        "request_type" : "POST"
                    },

                    "check_task_progress_request_parameters" :
                    {
                        "url" : "/browser/addmultipledevicesprogress/"
                    }
                };

                var before_start_add_single_device = function()
                {
                    $(show_add_single_device_message_tag_id).text("In progress " + device_name);
                    $(show_add_single_device_udid_tag_id).text(device_udid);
                }

                var add_device_async_task_processor = new AsyncTaskProcessor(start_add_single_device_parameters, before_start_add_single_device, after_finish_add_single_device);
                add_device_async_task_processor.start_task();

            }
        );
    }
);

$(document).ready(
    function(event)
    {
        $("#addmultipledevicesform").submit(
        //$("#adddeviceslistform").change(
            function(event)
            {
                event.preventDefault();

                var current_page = $("#current_page").text();
                var per_page = $("option:selected").val();

                var form_data = new FormData();
                files = $("#deviceslistfile")[0].files;
                if (files["length"] == 1)
                {
                    form_data.append('devices_list_file', files[0]);
                }

                var start_add_multiple_devices_parameters =
                {
                    "start_task_request_parameters" :
                    {
                        "url" : "/browser/startaddmultipledevices/",
                        "content_type" : false,
                        "data" : form_data,
                        "request_type" : "POST",
                        "cache" : false,
                        "process_data" : false
                    },

                    "check_task_progress_request_parameters" :
                    {
                        "url" : "/browser/addmultipledevicesprogress/"
                    }
                };
               
                var add_multiple_devices_async_task_processor = new AsyncTaskProcessor(start_add_multiple_devices_parameters, before_start_add_multiple_devices, after_finish_add_multiple_devices);
                add_multiple_devices_async_task_processor.start_task();

            }
        );
    }
);

$(document).ready(
    function()
    {
        $("#devicesperpage").change(
            function()
            {
                var per_page = $("option:selected").val()
                var current_page = $("#current_page").text();

                get_item_list("#devicelist", "#pagination", "/browser/getdeviceslist/", {"per_page" : per_page, "page_num" : current_page});
            }
        );
    }
);
