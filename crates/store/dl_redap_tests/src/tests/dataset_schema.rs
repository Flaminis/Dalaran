use dl_protos::cloud::v1alpha1::GetDatasetSchemaRequest;
use dl_protos::cloud::v1alpha1::dalaran_cloud_service_server::DalaranCloudService;
use dl_protos::headers::DalaranHeadersInjectorExt as _;

use super::common::{
    DalaranCloudServiceExt as _, DataSourcesDefinition, LayerDefinition, entry_name,
};
use crate::SchemaTestExt as _;

pub async fn simple_dataset_schema(service: impl DalaranCloudService) {
    let data_sources_def = DataSourcesDefinition::new_with_tuid_prefix(
        1,
        [
            LayerDefinition::simple("my_segment_id1", &["my/entity", "my/other/entity"]),
            LayerDefinition::simple("my_segment_id2", &["my/entity"]),
            LayerDefinition::simple(
                "my_segment_id3",
                &["my/entity", "another/one", "yet/another/one"],
            ),
        ],
    );

    let dataset_name = "my_dataset1";
    service.create_dataset_entry_with_name(dataset_name).await;
    service
        .register_with_dataset_name_blocking(dataset_name, data_sources_def.to_data_sources())
        .await;

    dataset_schema_snapshot(&service, dataset_name, "simple_dataset").await;
}

pub async fn empty_dataset_schema(service: impl DalaranCloudService) {
    let dataset_name = "empty_dataset";
    service.create_dataset_entry_with_name(dataset_name).await;

    dataset_schema_snapshot(&service, dataset_name, "empty_dataset").await;
}

// ---

async fn dataset_schema_snapshot(
    service: &impl DalaranCloudService,
    dataset_name: &str,
    snapshot_name: &str,
) {
    let schema = service
        .get_dataset_schema(
            tonic::Request::new(GetDatasetSchemaRequest {})
                .with_entry_name(entry_name(dataset_name)),
        )
        .await
        .unwrap()
        .into_inner()
        .schema()
        .unwrap();

    insta::assert_snapshot!(format!("{snapshot_name}_schema"), schema.format_snapshot());
}
