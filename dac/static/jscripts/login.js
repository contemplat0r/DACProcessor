var poll_period = 1000;
var timeout_duration = 0.05;

var complete_auth = function()
{
    console.log($(location).attr("host"));
    var origin = $(location).attr("origin");
    console.log(origin);
    window.location.replace(origin + "/users/profile/");
};

var check_auth_progress =  function(task_id, user_udid)
{
    console.log("Call check_auth_progress");
    if (task_id != undefined && task_id != null && task_id !=""  && user_udid != undefined && user_udid != null && user_udid != "")
    {
        var check_status = function()
        {
            console.log("Call check_status");
            $.ajax(
                {
                    url: "/users/authprogress/",
                    contentType: "application/json; charset=utf-8",
                    data: {"task_id" : task_id, "user_id" : user_udid},
                    type: "GET",
                    success: function(result)
                    {
                        if (result.state == "notready")
                        {
                            console.log("task not ready");
                        }
                        else if (result.state == "ready")
                        {
                            clearInterval(interval_id);
                            if (result.value == "auth success")
                            {
                                $("#authmessage").text("Auth success");
                                complete_auth();
                            }
                            else if (result.value == "not authorised")
                            {
                                $("#authmessage").text("Wrong user identifier or password");
                            }
                            else if (result.value == "")
                            {
                                $("#authmessage").text("Error by authorisation");
                            }
                            else
                            {
                                console.log("Unknown auth result value");
                            }
                        }
                        else
                        {
                            clearInterval(interval_id);
                            console.log("check_auth_progress, unknown task state: " + result.state);
                        }
                    },
                    error: function(thrownError)
                    {
                        clearInterval(interval_id);
                        console.log("auth progress check error: " + thrownError);
                    }
                }
            );
        }
        setTimeout(check_status, timeout_duration);
        var interval_id = setInterval(check_status, poll_period);
    }
};


$(document).ready(
    function()
    {
        $("#authform").submit(
            function(event)
            {
                event.preventDefault();
                $("#authmessage").text("user auth in progress...");
                $.ajax(
                    {
                        url: "/users/startauth/",
                        type: "POST",
                        data: $("#authform").serialize(),
                        success: function(result)
                        {

                            console.log("task_id: " + result.task_id);
                            console.log("user_uid: " + result.user_uid);
                            var task_id = result.task_id;
                            var user_uid = result.user_uid;
                            if (task_id != "" && user_uid != "")
                            {
                                console.log("That is call authprogress");
                                check_auth_progress(task_id, user_uid);
                            }
                            else
                            {
                                console.log("Wrong task_id or user_uid");
                            }
                        },
                        error: function(thrown_error)
                        {
                            console.log("Auth user check errror: " + thrown_error);
                        }
                    }
                );
            }
        );
    }
);

