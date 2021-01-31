jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

    $(document).ajaxStop(function(){
        // reactivation of the button
        $('#update_activities').removeClass('disabled')

        $("#circle_loading").hide()

        // In the case where there is no activity in base at the start
        $(".info_activities").show()
        $(".no_activities").hide()

    })


    $('#update_activities').on( 'click', function(e){
        $('#update_activities').addClass('disabled')
        $('.no_new_activities').css("display", "none")
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/get_new_activities'
        }
        $.ajax(options).done(response => {
            if(response.activities_added > 0){
                $(".activities_in_base").text(response.activities_in_base)
                $(".name_last_activity").text(response.name_last_activity)
                $(".date_last_activity").text(response.date_last_activity)
            } else {
                $("<p class='no_new_activities'> Aucune nouvelle activitée à charger </p>").insertAfter("#update_activities")
            }
        })
    });
})