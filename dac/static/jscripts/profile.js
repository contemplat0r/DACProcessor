var profile_id = get_object_id("#profileid", ":");

var show_message_tag_id = "#update_all_message";

var is_session_storage_available = function()
{
    return window.sessionStorage != undefined;
}

var session_storage_available = is_session_storage_available();

var session_storage;

if (session_storage_available)
{
    session_storage = window.sessionStorage;
}

window.onload = function()
{
    var per_page;
    var select_devices_condition;
    var page_num;
    console.log("per_page before get saved in session_storage: " + per_page);
    if (session_storage_available)
    {
        per_page = session_storage.getItem("saved_profile_devices_per_page");
        page_num = session_storage.getItem("saved_profile_devices_page_num");
        select_devices_condition = session_storage.getItem("saved_profile_devices_select_devices_condition");
        session_storage.removeItem("saved_profile_devices_per_page");
        session_storage.removeItem("saved_profile_devices_select_devices_condition");
        session_storage.removeItem("saved_profile_devices_page_num");
        console.log("per_page: " + per_page);
    }
    console.log("is_session_storage_available: " + is_session_storage_available());
    if (per_page == null || per_page == undefined)
    {
        per_page = $("#devicesperpage option:selected").val();
    }
    else
    {
        $("#devicesperpage").val(per_page);
    }
    if (select_devices_condition == null || select_devices_condition == undefined)
    {
        select_devices_condition = $("#select_devices_condition option:selected").val();
    }
    else
    {
        $("#select_devices_condition").val(select_devices_condition);
    }
    if (page_num == null || page_num == undefined)
    {
        page_num = 1;
    }
    console.log("window.onload, per_page: " + per_page + " select_devices_condition: " + select_devices_condition + " page_num: " + page_num);
    var profile_id = get_object_id("#profileid", ":");

    get_item_list("#deviceslist", "#pagination", "/browser/getprofiledeviceslist/", {"per_page" : per_page, "page_num" : page_num, "filter_predicate" : profile_id, "select_devices_condition" : select_devices_condition});
}

$(document).on("click", ".page_link", function(event)
    {
        event.preventDefault();

        var per_page = $("#devicesperpage option:selected").val();
        var page_num = get_page_num(this);
        var select_devices_condition = $("#select_devices_condition option:selected").val();

        get_item_list("#deviceslist", "#pagination", "/browser/getprofiledeviceslist/", {"per_page" : per_page, "page_num" : page_num, "filter_predicate" : profile_id, "select_devices_condition" : select_devices_condition});
    }
);

$(document).ready(
    function()
    {
        $("#devicesperpage").change(
            function()
            {
                var per_page = $("#devicesperpage option:selected").val()
                var current_page = $("#current_page").text();
                var select_devices_condition = $("#select_devices_condition option:selected").val();

                get_item_list("#deviceslist", "#pagination", "/browser/getprofiledeviceslist/", {"per_page" : per_page, "page_num" : current_page, "filter_predicate" : profile_id, "select_devices_condition" : select_devices_condition});
            }
        );
    }
);

$(document).ready(
    function()
    {
        $("#select_devices_condition").change(
            function()
            {
                var per_page = $("#devicesperpage option:selected").val()
                var current_page = $("#current_page").text();
                var select_devices_condition = $("#select_devices_condition option:selected").val();
                
                get_item_list("#deviceslist", "#pagination", "/browser/getprofiledeviceslist/", {"per_page" : per_page, "page_num" : current_page, "filter_predicate" : profile_id, "select_devices_condition" : select_devices_condition});
            }
        );
    }
);

var before_start_edit_profile = function()
{
    $("#profile_edit_process_message").text("Start processing profile...");
}


$(document).ready(
    function()
    {
        $("#profileeditform").submit(
            function(event)
            {
                event.preventDefault();

                var edit_profile_parameters =
                {
                    "start_task_request_parameters" :
                    {
                        "url" : "/browser/starteditprofile/",
                        "content_type" : "application/x-www-form-urlencoded",
                        "data" : $("#profileeditform").serialize(),
                        "request_type" : "POST"
                    },

                    "check_task_progress_request_parameters" :
                    {
                        "url" : "/browser/editprofileprogress/"
                    }
                };

                var edit_profile_async_task_processor = new AsyncTaskProcessor(edit_profile_parameters, before_start_edit_profile, after_finish_edit_profile);
                edit_profile_async_task_processor.start_task();

            }
        );
    }
);

var complete_edit_profile = function(profiles_edit_result)
{
    console.log("call complete_edit_profile");
    var success_occured = false;
    var unsuccess_occured = false;


    var new_profile_id;
    var profiles_edit_result_len = 0;
    var old_profile_id;
    var edited_profiles = {};

    for (var key in profiles_edit_result)
    {
        old_profile_id = key;
        profiles_edit_result_len = profiles_edit_result_len + 1;
        var profile_edit_result = profiles_edit_result[key];
        console.log("profile key: " + key + " profile edit result value: " + profile_edit_result);
        var name = profile_edit_result["profile_name"];
        new_profile_id = profile_edit_result["new_profile_id"]
        var success = profile_edit_result["success"];
        console.log("complete_edit_profile, for cycle, success: " + success);
        if (success == true)
        {
            console.log("check success: true");
            edited_profiles[key] = new_profile_id;
        }
        if (success == false)
        {
            console.log("check success: false");
        }

        if (success == true && success_occured == false)
        {
            success_occured = true;
        }
        if (success == false && unsuccess_occured == false)
        {
            unsuccess_occured == true;
        }

        console.log("name: " + name + " success: " + success + " new_profile_id: " + new_profile_id);
    }

    console.log("old profile id = " + old_profile_id);

    console.log("success_occured: " + success_occured);
    console.log("unsuccess_occured: " + unsuccess_occured);

    if (profiles_edit_result_len == 0)
    {
        $("#profile_edit_process_message").text("Profile processing error. May be Apple site connection problems");
    }
    else
    {
        if (unsuccess_occured)
        {
            $("#profile_edit_process_message").text("Profile processed unsuccessfuly.");
        }
        else if (success_occured)
        {

            $("#profile_edit_process_message").text("Profile processed successfuly.");
            if (new_profile_id != undefined)
            {
                var per_page = $("#devicesperpage option:selected").val()
                console.log("complete_edit_profile, per_page: " + per_page);
                var current_page = $("#current_page").text();
                var profile_id = $("#profile_id").val();
                var select_devices_condition = $("#select_devices_condition option:selected").val();

                var after_finish_replace_edited_profile = function(edit_result)
                {
                    var replace_success = edit_result.result_value;
                    if (replace_success != null)
                    {
                        console.log("check_replace_edited_profiles, result_value: ", replace_success);
                        if (replace_success)
                        {
                            //complete_replace_edited_profiles();
                            console.log("Call reload_profile_devices_list");
                            var origin = $(location).attr("origin");
                            session_storage.setItem("saved_profile_devices_per_page", per_page.toString());
                            session_storage.setItem("saved_profile_devices_page_num", current_page.toString());
                            session_storage.setItem("saved_profile_devices_select_devices_condition", select_devices_condition.toString());

                            window.location.replace(origin + "/browser/profile/" + new_profile_id);

                        }
                        else
                        {
                            //$(show_message_tag_id).text(unsuccess_replace_profiles_text);
                            $(show_message_tag_id).text("Unsuccess replace edited profiles");
                        }
                    }
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

                var replace_edited_profile_async_task_processor = new AsyncTaskProcessor(replace_edited_profiles_parameters, before_start_replace_edited_profiles, after_finish_replace_edited_profile);
                replace_edited_profile_async_task_processor.start_task();

            }
        }
        else
        {
            $("#profile_edit_process_message").text("Profile processing unknown state.");
        }
    }
}

var before_start_replace_edited_profiles = function(edited_profiles)
{
    $(show_message_tag_id).text("Replace edited profiles ...");
    
    console.log("start_replace_edited_profiles");
    console.log("start_replace_edited_profiles: " + edited_profiles);
}

var after_finish_edit_profile = function(edit_result)
{
    var result_value = edit_result.result_value;
    if (result_value != null)
    {
        console.log("Before call complete_edit_profile:");
        complete_edit_profile(result_value);
    }
    else
    {
        $("#profile_edit_process_message").text("Error by edit profile");
    }

}
