jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

    $(document).ajaxStop(function(){
        $("#circle_loading").hide()
        // In the case where there is no activity in base at the start
        $("#info_when_no_activities").show()
        $(".no_activities").hide()

    })


    $('#check_activities').on( 'click', function(e){
        $('#check_activities').addClass('disabled')
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/get_new_activities'
        }
        $.ajax(options).done(response => {
            if(response.activities_added > 0){
                $(".activities_in_base").text(response.activities_in_base)
                $(".name_last_activity").text(response.name_last_activity)
                $(".date_last_activity").text(response.format_date_last_activity)
            } else {
                $("<p> Aucune nouvelle activitée à charger </p>").insertAfter("#check_activities")
            }
        })
    });
})