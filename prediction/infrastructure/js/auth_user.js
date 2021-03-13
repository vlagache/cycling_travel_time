jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

    $(document).ajaxStop(function(){
        $("#circle_loading").hide()
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
                $(".date_last_activity").text('réalisé à ' + response.date_last_activity)
            } else {
                $("<p class='no_new_activities'> Aucune nouvelle activitée à charger </p>").insertAfter("#update_activities")
            }
            $(".info_last_activity").show()
            $(".no_activities").hide()
            $('#update_activities').removeClass('disabled')
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
                $(".date_last_route").text('crée le ' + response.date_last_route)
            } else {
                $("<p class='no_new_routes'> Aucune nouvelle route à charger </p>").insertAfter("#update_routes")
            }
            $(".info_last_route").show()
            $(".no_routes").hide()
            $('#update_routes').removeClass('disabled')
        })
    });

// Train Models
    $('#update_models').on( 'click', function(e){
        $('#update_models').addClass('disabled')
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/train_models'
        }
        $.ajax(options).done(response => {
            $(".models_in_base").text(response.models_in_base)
            $(".date_last_model").text('entrainé le ' + response.date_last_model)
            $(".info_last_model").show()
            $(".no_models").hide()
            $('#update_models').removeClass('disabled')
        })
    });


})