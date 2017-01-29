var $ontologiSelect = $('#id_ontology_id');
var $conceptSelect = $('#id_concept_name');
$ontologiSelect.append($('<option>'), {text: 'loding...'});
$ontologiSelect.on('change', function(){
    $conceptSelect.val(null).trigger("change");
});
$conceptSelect.append($('<option>'), {text: 'loding...'});

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
        url: "http://data.bioontology.org/search",
        dataType: 'json',
        beforeSend: beforeSend,
        delay: 250,
        data: function (params) {
            return {
                q: params.term,
                page: params.page,
                ontologies: $ontologiSelect.val(),
            };
        },
        processResults: function (data, params) {
            return {
                results: _.map(data.collection, function(item){
                    item.id = item['@id'];
                    item.text = item.prefLabel;
                    return item;
                }),
                pagination: data.links.nextPage
            };
        },
        cache: false,
    },
    escapeMarkup: function (markup) { return markup; },
    templateResult: function(data) {
        if(data.loading) {
            return data.text;
        }
        var definition = data.definition ? data.definition[0] : '';
        return "<p><b>" + data.text + "</b>" + definition + "</p>";
    },
    templateSelection: function(data) { return data.text; },
    minimumInputLength: 1,
});

