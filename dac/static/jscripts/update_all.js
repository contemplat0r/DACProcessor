message_tag_id = "#progress-indicator";

var before_start_all_update = function(result)
{
    $(message_tag_id).text(start_all_update_message_text);
};

var after_finish_all_update = function(result)
{
    var result_value = result.result_value;
    var retrieved_devices_count = parseInt(result_value["retrieved_devices_count"]);
    var retrieved_profiles_count = parseInt(result_value["retrieved_profiles_count"]);
    if (retrieved_devices_count == -1 && retrieved_profiles_count == -1)
    {
        $(message_tag_id).text(error_all_update_message_text);
    }
    else
    {
        $(message_tag_id).text(complete_all_update_message_text);
    }
};



$(document).ready(
    function()
    {
        $(".form-horizontal").submit(
            function(event)
            {
                event.preventDefault();
                console.log("Start all update");
                var all_update_async_task_processor = new AsyncTaskProcessor(start_all_update_parameters, before_start_all_update, after_finish_all_update);
                all_update_async_task_processor.start_task();

            }
        );
    }
);


