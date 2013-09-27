window.LTI = (function () {
    // Function initialize(element)
    //
    // Initialize the LTI module.
    function initialize(element) {
        var form;
        // In cms (Studio) the element is already a jQuery object. In lms it is
        // a DOM object.
        //
        // To make sure that there is no error, we pass it through the $()
        // function. This will make it a jQuery object if it isn't already so.
        element = $(element);

        form = element.find('.ltiLaunchForm');

        var open_in_a_new_page = JSON.parse(element.find('.lti').data('open_in_a_new_page'));

        // If the Form's action attribute is set (i.e. we can perform a normal submit),
        // then we submit the form immediately or when user will click on a link
        // (depending on instance settings) and make the frame shown.
        if (open_in_a_new_page === true) {
            element.find('.link_lti_new_window').click(function(){
                form.submit();
            });
        }
        else if (open_in_a_new_page === false) {
            form.submit();
        }
    }

    return initialize;
}());
