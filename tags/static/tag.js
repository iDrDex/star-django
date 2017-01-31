var $conceptName = $('#id_concept_name');
var $ontologiSelect = $('#id_ontology_id');
var $conceptSelect = $('#id_concept_full_id');

$.ajax({
    url: "http://data.bioontology.org/ontologies",
    dataType: "json",
    beforeSend: function (xhr){
        xhr.setRequestHeader("Authorization", "apikey token="+window.BIOPORTAL_API_KEY);
        },
    }).then(function(data){
        var val = $ontologiSelect.val();
        $ontologiSelect.html('');
        $ontologiSelect.select2({
            matcher: function(params, data) {
                if ($.trim(params.term) === '') {
                    return data;
                }
                var term = params.term.toUpperCase();
                var original = data.text.toUpperCase() + " " + data.id.toUpperCase();

                if (original.indexOf(term) > -1) {
                    return data;
                }

                return null;
            },
            templateSelection: function(data) { return data.id + " (" + data.text + ")"; },
            templateResult: function(data) { return data.id + " (" + data.text + ")"; },
            data: _.map(data, function(ontology){
                return {
                    id: ontology.acronym,
                    text: ontology.name
                };
            }),
        });
        $ontologiSelect.val(val).trigger('change');
        $ontologiSelect.on('change', function(e){
            var newOntology = e.target.value;
            var conceptOntology = ($conceptSelect.select2('data')[0] || {}).ontology;
            if (newOntology !== conceptOntology) {
                $conceptSelect.val(null).trigger("change");
            }
        });
        populateConceptValue();
});

$conceptSelect.select2({
    ajax: {
        url: "http://bioportal.bioontology.org/search/json_search/",
        dataType: "jsonp",
        delay: 250,
        data: function (params) {
            return {
                q: params.term,
                target_property: "name",
                ontologies: $ontologiSelect.val(),
                response: "json",
            };
        },
        processResults: function (data, params) {
            var results = data.data.split('~!~')
                .filter(function(item){ return item !== "";})
                .map(function(itemString){
                    var item = itemString.split('|');
                    return {
                        text: item[0],
                        id: item[1],
                        ontology: item[3],
                        definition: item[7],
                    };
                });
            return {
                results: results,
            };
        },
        cache: false,
    },
    escapeMarkup: function (markup) { return markup; },
    templateResult: function(data) {
        if(data.loading) {
            return data.text;
        }
        return "<p><b>" + data.text + "</b> " + data.definition + "</p>";
    },
    templateSelection: function(data) { return data.text; },
    minimumInputLength: 1,
});

function populateConceptValue() {
    $conceptLink.html('');
    var data = $conceptSelect.select2('data')[0];
    if (data) {
        $conceptName.val(data.text);
        if (data.ontology) {
            $ontologiSelect.val(data.ontology).trigger('change');
        }
        $conceptLink.attr({ href: data.id, target: "_blank"}).html(data.id);
    }
}

$conceptSelect.on('change', populateConceptValue);
$conceptSelect.parent().append("<b>Concept:</b> <a id='conceptLink'></p>");
var $conceptLink = $('#conceptLink');
