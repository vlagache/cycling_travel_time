jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

    $(document).ajaxStop(function(){
        // reactivation of the button
        $('#update_activities').removeClass('disabled')
        $('#update_routes').removeClass('disabled')

        $("#circle_loading").hide()

        // In the case where there is no activity in base at the start
        $(".info_activities").show()
        $(".no_activities").hide()

        $(".info_routes").show()
        $(".no_routes").hide()

    })

//    Update Activities

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

//    Update Routes

    $('#update_routes').on( 'click', function(e){
        $('#update_routes').addClass('disabled')
        $('.no_new_routes').css("display", "none")
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/get_new_routes'
        }
        $.ajax(options).done(response => {
            if(response.routes_added > 0){
                $(".routes_in_base").text(response.routes_in_base)
                $(".name_last_route").text(response.name_last_route)
                $(".date_last_route").text(response.date_last_route)
            } else {
                $("<p class='no_new_routes'> Aucune nouvelle route à charger </p>").insertAfter("#update_routes")
            }
        })
    });

//    Select Routes
     $('select').select();

     $('#segmentation').on( 'click', function(e){
        console.log($('#route_choice option:selected').val());
     });
})