window.onload = function()
{
    var per_page = $("#profilesperpage option:selected").val();

    get_item_list("#profileslist", "#pagination", "/browser/getprofileslist/", {"per_page" : per_page, "page_num" : 1});
}

$(document).on("click", ".page_link", function(event)
    {
        event.preventDefault();
        
        var per_page = $("#profilesperpage option:selected").val();
        var page_num = get_page_num(this);
        get_item_list("#profileslist", "#pagination", "/browser/getprofileslist/", {"per_page" : per_page, "page_num" : page_num});
    }
);

$(document).ready(
    function()
    {
        $("#profilesperpage").change(
            function()
            {
                var per_page = $("option:selected").val()
                var current_page = $("#current_page").text();

                get_item_list("#profileslist", "#pagination", "/browser/getprofileslist/", {"per_page" : per_page, "page_num" : current_page});
            }
        );
    }
);
