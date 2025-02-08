<script>
    function highlightText(id) {
        if(id.startsWith("doctor_")){
            id = id.substr(7);
            // console.log(id);
        }
        var elements = document.querySelectorAll('#'+id);
        elements.forEach(function(element) {
            element.classList.add('highlight');
        });
        var elements = document.querySelectorAll('#doctor_'+id);
        elements.forEach(function(element) {
            element.classList.add('highlight');
        });
    }

    function removeHighlight(id) {
        if(id.startsWith("doctor_")){
            id = id.substr(7);
            // console.log(id);
        }
        var elements = document.querySelectorAll('#'+id);

        elements.forEach(function(element) {
            element.classList.remove('highlight');
        });
        
        var elements = document.querySelectorAll('#doctor_'+id);
        elements.forEach(function(element) {
            element.classList.remove('highlight');
        });
    }

    function goToHere(id){
        if(id.startsWith("doctor_")){
            id = id.substr(7);
            // console.log(id);
        }

        var elements = document.querySelectorAll('#'+id);
        var need_elements = new Array(elements[elements.length - 1],document.querySelector('#doctor_'+id));
        need_elements.forEach(function(element) {
            element.scrollIntoView()
        });

        var title_elements = document.querySelectorAll('#title_'+id);
        // console.log(title_elements)
        title_elements.forEach(function(element) {
            element.scrollIntoView()
        });
    }

    function goToDoctorHere(id){
        if(id.startsWith("doctor_")){
            id = id.substr(7);
            console.log(id);
        }

        var elements = document.querySelectorAll('#'+id);
        var need_elements = new Array(elements[elements.length - 1],document.querySelector('#doctor_'+id));
        need_elements.forEach(function(element) {
            console.log(element);
            console.log('element');
            element.scrollIntoView()
        });
    }
</script>