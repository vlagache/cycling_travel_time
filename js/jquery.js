jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

    $(document).ajaxStop(function(){
        $("#circle_loading").hide()
    })


    $('#check_activities').on( 'click', function(e){
        $('#check_activities').addClass('disabled')
        var number_of_activities = $(".activities_in_base").text()
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/debug'
        }
        $.ajax(options).done(response => {
            if(response.number_of_new_activities > 0){
                console.log(response.number_of_new_activities)
                console.log(number_of_activities)
                var new_number_of_activities = (+response.number_of_new_activities) + (+number_of_activities)
                $(".activities_in_base").text(new_number_of_activities)
                $(".name_last_activity").text(response.name_last_activity)
                $(".date_last_activity").text(response.date_last_activity)
            } else {
                $("<p> Aucune nouvelle activitée à charger </p>").insertAfter("#check_activities")
            }
        })
    });
})