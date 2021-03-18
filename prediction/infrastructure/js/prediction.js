jQuery(document).ready(function(){

    // Nav Bar

    switch (window.location.pathname) {
        case '/authenticated_user':
            $('.authenticated_user').addClass('active')
            break;
        case '/road_prediction':
            $('.road_prediction').addClass('active')
            break;
    }

    $(document).ajaxStart(function(){
        $("#road_prediction").css("opacity",0.2)
        $("#circle_loading").show()
        $(".button").addClass('disabled')
    })

    $(document).ajaxStop(function(){
        $("#road_prediction").css("opacity",1)
        $("#circle_loading").hide()
        $(".button").removeClass('disabled')
    })

//    Select Routes
     $('select').select();

     $('#checkbox_btn').on( 'click', function(e){
        virtual_ride = $('#virtual_ride').prop('checked')
        virtual_ride
        test = 1
        e.preventDefault();
        let options = {
            method:'GET',
            url:'/virtual_ride?var=' + virtual_ride + '&test=' + test
        }
        $.ajax(options).done(response => {
            console.log(response)

        })

     })

     $('#prediction_btn').on( 'click', function(e){
        if ($('#route_choice option:selected').val() != 0) {
            $('#prediction_btn').addClass('disabled')
            $('.prediction_time').css('opacity',0)

            route_id = $('#route_choice option:selected').val()
            virtual_ride = $('#virtual_ride').prop('checked')
            e.preventDefault();
            let options = {
                method:'GET',
                url:'/get_prediction?route_id=' + route_id + '&virtual_ride=' + virtual_ride
            }
            $.ajax(options).done(response => {
                if(response == null) {
                    $(".info_prediction").text("Pas de modèles entrainés")
                    /* After a fadeTo opacity = 0  */
                    $(".info_prediction").css("opacity",1)
                    $(".info_prediction").delay(5000).fadeTo('slow',0)
                } else {
                    $(".prediction_time").text(
                    response.hours+"h"+response.minutes+"min"+response.seconds+"s - " + response.avg_speed_kmh + " km/h")
//                    $('.prediction_time').show()
                    $('.prediction_time').css('opacity',1)
                    $(".info_prediction").hide()
                }
            })
        } else {
            $(".info_prediction").text("Pas de route sélectionnée")
            /* After a fadeTo opacity = 0  */
            $(".info_prediction").css("opacity",1)
            $(".info_prediction").delay(5000).fadeTo('slow',0)
        }
     });

//     Loading Map of Route
     $('#route_choice').on('change', function(e){
        var value = $(this).val()
//        $('.prediction_time').hide()
        $('.prediction_time').css('opacity',0)
        $(".info_prediction").css('opacity',0)
        e.preventDefault();
        get_map(value);
        get_segmentation_map(value);
        $('#maps_content').fadeIn('slow')
     });


     var get_map = (function(value){
        let options = {
            method:'GET',
            url: '/get_map?route_id=' + value
        }
        $.ajax(options).done(response => {
            $('#map_route').html(response)

        });
     });

     var get_segmentation_map = (function(value){
        let options = {
            method:'GET',
            url: '/get_segmentation_map?route_id=' + value
        }
        $.ajax(options).done(response => {
            $('#map_segmentation_route').html(response)
        })
     });
})