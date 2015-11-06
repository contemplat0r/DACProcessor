var start_ldap_sync_message_text = "Synchronization users with LDAP...";
var complete_ldap_sync_message_text = "Complete users synchronization with LDAP";
var message_tag_id = "#ldapsyncmessage";

var start_ldap_sync_parameters =
{
    "start_task_request_parameters" :
    {
        "url" : "/users/startldapsync/",
        "content_type" : "application/json; charset=utf-8",
        "request_type" : "POST",
        "data" : "",
    },

    "check_task_progress_request_parameters" :
    {
        "url" : "/users/ldapsyncprogress/"
    }
};


var reload_users_list = function(records_per_page, current_page, items_view_url)
{
    get_item_list("#userslist", "#pagination", items_view_url, {"per_page" : records_per_page, "page_num" : current_page});
}

var before_start_ldap_sync = function()
{
    $(message_tag_id).text(start_ldap_sync_message_text);
};

var after_finish_ldap_sync = function(ldap_sync_result)
{
    $(message_tag_id).text(complete_ldap_sync_message_text);
    var current_page = $("#current_page").text();
    var per_page = $("#usersperpage option:selected").val();
    reload_users_list(per_page, current_page, "/users/getuserslist/");
};

window.onload = function()
{
    var per_page = $("#usersperpage option:selected").val();
    get_item_list("#userslist", "#pagination", "/users/getuserslist/", {"per_page" : per_page, "page_num" : 1});
}

$(document).ready(
    function()
    {
        $("#registeruserform").submit(
            function(event)
            {
                event.preventDefault();
                $("#registerusermessage").text("registering user...");
                $.ajax(
                    {
                        url: "/users/adduser/",
                        type: "POST",
                        data: $("#registeruserform").serialize(),
                        success: function(result)
                        {

                            console.log("completion_code: " + result.completion_code);
                            console.log(result)
                            if (result.completion_code == "success")
                            {
                                $("#registerusermessage").text("user registered");
                                var current_page = $("#current_page").text();
                                var per_page = $("#usersperpage option:selected").val();

                                get_item_list("#userslist", "#pagination", "/users/getuserslist/", {"per_page" : per_page, "page_num" : current_page});
                            }
                            else if (result.completion_code == "exists")
                            {
                                $("#registerusermessage").text("user with this uid already exists");
                            }
                            else if (result.completion_code == "fail")
                            {
                                $("#registerusermessage").text("error occured by user registration");
                            }

                        },
                        error: function(jqXHR, statusText, thrownError)
                        {
                            ajax_error_processor(jqXHR, statusText, thrownError);
                        }
                    }
                );
            }
        );
    }
);

$(document).ready(
    function()
    {
        $("#ldapsyncform").submit(
            function(event)
            {
                event.preventDefault();

                var ldap_sync_async_task_processor = new AsyncTaskProcessor(start_ldap_sync_parameters, before_start_ldap_sync, after_finish_ldap_sync);
                ldap_sync_async_task_processor.start_task();

            }
        );
    }
);


$(document).ready(
    function()
    {
        $("#userslistform").submit(
            function(event)
            {
                event.preventDefault();
                $("#userslistupdatemsg").text("refreshing users list...");
                $.ajax(
                    {
                        url: "/users/updateuserslist/",
                        type: 'POST',
                        data: $("#userslistform").serialize(),
                        success: function(result)
                        {

                            console.log("completion_code: " + result.completion_code);
                            console.log(result)
                            if (result.completion_code == "success")
                            {
                                $("#userslistupdatemsg").text("");
                                var current_page = $("#current_page").text();
                                var per_page = $("#usersperpage option:selected").val();

                                get_item_list("#userslist", "#pagination", "/users/getuserslist/", {"per_page" : per_page, "page_num" : current_page});
                            }
                        },
                        error: function(jqXHR, statusText, thrownError)
                        {
                            console.log("Update users check errror: " + thrown_error);
                            ajax_error_processor(jqXHR, statusText, thrownError);
                        }
                    }
                );
            }
        );
    }
);

$(document).on("click", ".page_link", function(event)
    {
        event.preventDefault();
        $("#registerusermessage").text("");
        $("#userslistupdatemsg").text("");
        $("#ldapsyncmessage").text("");
        
        var per_page = $("#usersperpage option:selected").val();
        var page_num = get_page_num(this);

        //console.log("Page num: " + page_num);
        get_item_list("#userslist", "#pagination", "/users/getuserslist/", {"per_page" : per_page, "page_num" : page_num});
    }
);

$(document).ready(
    function()
    {
        $("#usersperpage").change(
            function()
            {
                var current_page = $("#current_page").text();
                var per_page = $("#usersperpage option:selected").val();

                get_item_list("#userslist", "#pagination", "/users/getuserslist/", {"per_page" : per_page, "page_num" : current_page});
            }
        );
    }
);
