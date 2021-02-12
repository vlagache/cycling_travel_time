jQuery(document).ready(function(){

    $(document).ajaxStart(function(){
        $("#circle_loading").show()
    })

        $(document).ajaxStop(function(){
        // reactivation of the button
        $('#segmentation').removeClass('disabled')
        $("#circle_loading").hide()

    })

//    Select Routes
     $('select').select();

     $('#segmentation').on( 'click', function(e){
        $('#segmentation').addClass('disabled')
        route_id = $('#route_choice option:selected').val()
        e.preventDefault();
        let options = {
            method:'GET',
            url:'/test_segmentation?route_id=' + route_id
        }
        $.ajax(options).done(response => {
            $(".segmentation_info").text(response)
            console.log(response)
        })

//        console.log($('#route_choice option:selected').val());
     });

//     Loading Map of Route
     $('#route_choice').on('change', function(e){
        var value = $(this).val()
        $('#map_route').empty()
        e.preventDefault();
        let options = {
            method:'GET',
            url: '/get_map?route_id=' + value
        }
        $.ajax(options).done(response => {
            $('#map_route').append(response)
        })
     });

})