from django.db.models import Aggregate


class ArrayAgg(Aggregate):
    function = 'ARRAY_AGG'

    def convert_value(self, value, expression, connection, context):
        if not value:
            return []
        return value


class ArrayConcatUniq(ArrayAgg):
    function = 'ARRAY_CONCAT_UNIQ'


class ArrayConcat(ArrayAgg):
    function = 'ARRAY_CONCAT'
