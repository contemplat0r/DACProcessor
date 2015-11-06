console.log("load deviceprofiles");

var device_number = get_object_id("#deviceudid", ":");

var show_profiles_edit_message_tag_id = "#profiles_edit_process_message";

window.onload = function()
{
    var per_page = $("#profilesperpage option:selected").val();
    var device_id = $("#device_id").val();
    var select_profiles_condition = $("#select_profiles option:selected").val();

    console.log("per_page: " + per_page + " device_id: " + device_id + " select_profiles_condition: " + select_profiles_condition);
    get_item_list("#profileslist", "#pagination", "/browser/getdeviceprofileslist/", {"per_page" : per_page, "page_num" : 1, "filter_predicate" : device_number, "device_id" : device_id, "select_profiles_condition" : select_profiles_condition});
}



$(document).on("click", ".page_link", function(event)
    {
        event.preventDefault();
        var host_url = $(location).attr("origin");
        var full_href_url = this + "";
        var page_url_part = full_href_url.substr(host_url.length + 1);
        var per_page = $("#profilesperpage option:selected").val();
        var device_id = $("#device_id").val();
        var select_profiles_condition = $("#select_profiles option:selected").val();
 
        console.log("Page link click, per_page: " + per_page + " device_id: " + device_id + " select_profiles_condition: " + select_profiles_condition);
        get_item_list("#profileslist", "#pagination", "/browser/getdeviceprofileslist/", {"per_page" : per_page, "page_num" : page_url_part, "filter_predicate" : device_number, "device_id" : device_id, "select_profiles_condition" : select_profiles_condition});
    }
);

$(document).ready(
    function()
    {
        $("#profilesperpage").change(
            function()
            {
                var per_page = $("#profilesperpage option:selected").val()
                var current_page = $("#current_page").text();
                var device_id = $("#device_id").val();
                var select_profiles_condition = $("#select_profiles option:selected").val();

                console.log("per_page: " + per_page + " current_page: " + current_page + " device_id: " + device_id + " select_profiles_condition: " + select_profiles_condition);
                get_item_list("#profileslist", "#pagination", "/browser/getdeviceprofileslist/", {"per_page" : per_page, "page_num" : current_page, "filter_predicate" : device_number, "device_id" : device_id, "select_profiles_condition" : select_profiles_condition});
            }
        );
    }
);

$(document).ready(
    function()
    {
        $("#select_profiles").change(
            function()
            {
                var per_page = $("#profilesperpage option:selected").val()
                var current_page = $("#current_page").text();
                var device_id = $("#device_id").val();
                var select_profiles_condition = $("#select_profiles option:selected").val();
                /*if (select_profiles_condition == "1")
                {
                    console.log("select_profiles_condition == 1");
                    console.log($("#submit_edit_command").val());
                    //$("#submit_edit_command").val("- Remove from profiles");
                    $("#submit").val("- Remove from profiles");
                }
                else
                {
                    //$("#submit_edit_command").val("+ Add to profiles");
                    $("#submit").val("+ Add to profiles");
                    console.log("select_profiles_condition == 0");
                    console.log($("#submit_edit_command").val());
                }*/
                console.log("per_page: " + per_page + " current_page: " + current_page + " device_id: " + device_id + " select_profiles_condition: " + select_profiles_condition);

                get_item_list("#profileslist", "#pagination", "/browser/getdeviceprofileslist/", {"per_page" : per_page, "page_num" : current_page, "filter_predicate" : device_number, "device_id" : device_id, "select_profiles_condition" : select_profiles_condition});
            }
        );
    }
);

$(document).ready(
    function()
    {
        $("#profileseditform").submit(
            function(event)
            {
                event.preventDefault();

                var edit_profiles_parameters =
                {
                    "start_task_request_parameters" :
                    {
                        "url" : "/browser/starteditprofiles/",
                        "content_type" : "application/x-www-form-urlencoded",
                        "data" : $("#profileseditform").serialize(),
                        "request_type" : "POST"
                    },

                    "check_task_progress_request_parameters" :
                    {
                        "url" : "/browser/editprofilesprogress/"
                    }
                };

                var edit_profiles_async_task_processor = new AsyncTaskProcessor(edit_profiles_parameters, before_start_edit_profiles, after_finish_edit_profiles);
                edit_profiles_async_task_processor.start_task();

            }
        );
    }
);

var before_start_edit_profiles = function()
{
    $(show_profiles_edit_message_tag_id).text("Start processing profiles...");
}

var after_finish_edit_profiles = function(profiles_edit_result)
{
    profiles_edit_result = profiles_edit_result.result_value;
    console.log("call complete_edit_profiles");
    var success_occured = false;
    var unsuccess_occured = false;
    var unsucessful_processed_profiles = ""
    var profiles_edit_result_len = 0;
    var edited_profiles = {};
    for (var key in profiles_edit_result)
    {
        profiles_edit_result_len = profiles_edit_result_len + 1;
        profile_edit_result = profiles_edit_result[key];
        console.log("key: " + key + " value: " + profile_edit_result);
        var name = profile_edit_result["profile_name"];
        var success = profile_edit_result["success"];
        var new_profile_id = profile_edit_result["new_profile_id"]
        if (success == true)
        {  
            if (success_occured == false)
            {
                success_occured = true;
            }
            edited_profiles[key] = new_profile_id;
        }
        else if (success == false && unsuccess_occured == false)
        {
            unsuccess_occured == true;
            unsucessful_processed_profiles = unsucessful_processed_profiles + name + " ";
        }
    }

    if (profiles_edit_result_len == 0)
    {
        $(show_profiles_edit_message_tag_id).text("Profiles processing error. May be Apple site connection problems");
    }
    else
    {
        if (unsuccess_occured)
        {
            $(show_profiles_edit_message_tag_id).text("Profiles " + unsucessful_processed_profiles + "processed unsucessfuly.");
        }
        else
        {

            $(show_profiles_edit_message_tag_id).text("All profiles processed sucessfuly.");
        }

        if (success_occured)
        {
            console.log("complete_edit_profiles: success_occured");

            var per_page = $("#profilesperpage option:selected").val()
            console.log("complete_edit_profiles, per_page: " + per_page);
            var current_page = $("#current_page").text();
            var device_id = $("#device_id").val();
            var select_profiles_condition = $("#select_profiles option:selected").val();

            var after_finish_replace_edited_profiles = function(edit_result)
            {
                $(show_profiles_edit_message_tag_id).text("Complete replace edited profiles");
                console.log("call reload_device_profiles_list");
                console.log("per_page: " + per_page + " current_page: " + current_page + " device_id: " + device_id + " select_profiles_condition: " + select_profiles_condition);
                get_item_list("#profileslist", "#pagination", "/browser/getdeviceprofileslist/", {"per_page" : per_page, "page_num" : current_page, "filter_predicate" : device_number, "device_id" : device_id, "select_profiles_condition" : select_profiles_condition});

            }

            var replace_edited_profiles_parameters =
            {
                "start_task_request_parameters" :
                {
                    "url" : "/browser/startreplaceeditedprofiles/",
                    "content_type" : "application/json; charset=utf-8",
                    "data" : JSON.stringify(edited_profiles),
                    "request_type" : "POST"
                },

                "check_task_progress_request_parameters" :
                {
                    "url" : "/browser/replaceeditedprofilesprogress/"
                }
            };

            var replace_edited_profiles_async_task_processor = new AsyncTaskProcessor(replace_edited_profiles_parameters, before_start_replace_edited_profiles, after_finish_replace_edited_profiles);
            replace_edited_profiles_async_task_processor.start_task();
        }
    }
}

var before_start_replace_edited_profiles = function(edited_profiles)
{
    $(show_profiles_edit_message_tag_id).text("Replace edited profiles ...");
    
    console.log("start_replace_edited_profiles");
    console.log("start_replace_edited_profiles: " + edited_profiles);
}

