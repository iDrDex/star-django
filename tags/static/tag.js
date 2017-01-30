var $conceptName = $('#id_concept_name');

var $ontologiSelect = $('#id_ontology_id');
$ontologiSelect.append($('<option>'), {text: 'loding...'});
$ontologiSelect.on('change', function(){
    $conceptSelect.val(null).trigger("change");
});

var $conceptSelect = $('#id_concept_full_id');
$conceptSelect.append($('<option>'), {text: 'loding...'});
$conceptSelect.on('change', function(){
    $conceptName.val($conceptSelect.select2('data')[0].text);
});


function beforeSend(xhr){
    xhr.setRequestHeader ("Authorization", "apikey token=");
}

$.ajax({
    url: "http://data.bioontology.org/ontologies",
    dataType: "json",
    beforeSend: beforeSend,
    }).then(function(data){
        $ontologiSelect.select2({
            data: _.map(data, function(ontology){
                return {
                    id: ontology.acronym,
                    text: ontology.name
                };
            }),
        });
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
            var results = data.data.split('~!~').map(function(itemString){
                var item = itemString.split('|');
                return {
                    id: item[1],
                    text: item[0],
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

