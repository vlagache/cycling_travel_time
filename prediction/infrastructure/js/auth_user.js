jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#authenticated_user").css("opacity",0.2)
        $("#circle_loading").show()
        $(".button").addClass('disabled')
    })

    $(document).ajaxStop(function(){
        $("#authenticated_user").css("opacity",1)
        $("#circle_loading").hide()
        $(".button").removeClass('disabled')
    })

//    Update Activities

    $('#update_activities').on( 'click', function(e){
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
                $(".no_new_activities").text("Aucune nouvelle activitée à charger")
                /* After a fadeTo opacity = 0  */
                $(".no_new_activities").css("opacity",1)
                $(".no_new_activities").delay(5000).fadeTo('slow',0)
            }
            $(".info_last_activity").show()
            $(".no_activities").hide()
        })
    });

//    Update Routes

    $('#update_routes').on( 'click', function(e){
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
                $(".no_new_routes").text('Aucune nouvelle route à charger')
                /* After a fadeTo opacity = 0  */
                $(".no_new_routes").css("opacity",1)
                $(".no_new_routes").delay(5000).fadeTo('slow',0)
            }
            $(".info_last_route").show()
            $(".no_routes").hide()
        })
    });

// Train Models
    $('#update_models').on( 'click', function(e){
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/train_models'
        }
        $.ajax(options).done(response => {
            if(response == null) {
                $(".no_activities_for_train").text("Aucune activitée pour entrainer un modèle")
                /* After a fadeTo opacity = 0  */
                $(".no_activities_for_train").css("opacity",1)
                $(".no_activities_for_train").delay(5000).fadeTo('slow',0)
            } else {
                $(".models_in_base").text(response.models_in_base)
                $(".date_last_model").text('entrainé le ' + response.date_last_model)
                $(".info_last_model").show()
                $(".no_models").hide()
            }
        })
    });


})