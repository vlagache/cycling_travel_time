jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

        $(document).ajaxStop(function(){
        // reactivation of the button
        $('#prediction_btn').removeClass('disabled')
        $("#circle_loading").hide()

    })

//    Select Routes
     $('select').select();

     $('#prediction_btn').on( 'click', function(e){
        $('#prediction_btn').addClass('disabled')
        $('.prediction_time').hide()
        route_id = $('#route_choice option:selected').val()
        e.preventDefault();
        let options = {
            method:'GET',
            url:'/get_prediction?route_id=' + route_id
        }
        $.ajax(options).done(response => {
            if(response == null) {
                $(".prediction_time").text("Pas de modeles entrainés")
                $('.prediction_time').show()
            } else {
                $(".prediction_time").text(
                response.hours+"h"+response.minutes+"min"+response.seconds+"s , Vitesse : "+response.avg_speed_kmh+"km/h"
                )
                $('.prediction_time').show()
            }
        })
     });

//     Loading Map of Route
     $('#route_choice').on('change', function(e){
        var value = $(this).val()
        $('#map_route').empty()
        $('#map_segmentation_route').empty()
        $('#segments').empty()
        $('.prediction_time').hide()
        e.preventDefault();
        get_map(value);
        get_segmentation_map(value);
//        get_segmentation(value);
     });


     var get_map = (function(value){
        let options = {
            method:'GET',
            url: '/get_map?route_id=' + value
        }
        $.ajax(options).done(response => {
            $('#map_route').append(response)
        })
     });

     var get_segmentation_map = (function(value){
        let options = {
            method:'GET',
            url: '/get_segmentation_map?route_id=' + value
        }
        $.ajax(options).done(response => {
            $('#map_segmentation_route').append(response)
        })
     });

//     var get_segmentation=(function(value){
//        let options = {
//            method:'GET',
//            url: '/get_segmentation?route_id=' + value
//        }
//        $.ajax(options).done(response => {
//            $.each(response, function(index , segment){
//                $('#segments').append(
//                    "<p class='segment'> Segment " +  (index+1) + " : distance : " + segment.distance +
//                     " , altitude_gain " + segment.altitude_gain +", average_grade : "
//                     + segment.average_grade +  " </p>"
//                )
//            });
//        })
//     });



})