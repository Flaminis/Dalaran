This example will query for the first 10 rows of data in your recording of choice,
and display the results as a table in your terminal.

You can use one of your recordings, or grab one from our hosted examples, e.g.:
```bash
curl 'https://app.dalaran.dev/version/latest/examples/dna.dlr' -o - > /tmp/dna.dlr
```

The results can be filtered further by specifying an entity filter expression:
```bash
python dataframe_query.py my_recording.dlr /helix/structure/**\
```

```bash
python dataframe_query.py <path_to_dlr> [entity_path_filter]
```
