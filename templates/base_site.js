
// monkey with the positioning of the error messages in form fields.  As it is they are great for screen
// readers but difficult to style
Y.all('.field.error').each(function(field) {
    Y.Custom.positionFieldError(field);
});

// add some simple client-side validation to the search bar(s)
Y.all("form#search button").each(function (searchButton) {
    searchButton.on("click", function(e) {
        var form = searchButton.ancestor("form#search");
        var searchBox = form.one("input#id_q");
        var searchText = searchBox.get("value").trim();
        var error = null;

        if (searchText.length <= 1) {
            // invalid search query
            e.preventDefault();
            if (searchText.length == 0) {
                error = "Enter a search word or phrase";
            } else {
                error = "Type at least 2 characters in the search box";
            }
        } else if (searchText.length > 50) {
            error = "Too many characters.  Max is 50, you entered " + searchText.length
        }
        if (error) {
            e.preventDefault();
            var field = searchBox.ancestor(".field");
            Y.Custom.setFieldError(field, error, true); // error as a popup
        }
    });
});
