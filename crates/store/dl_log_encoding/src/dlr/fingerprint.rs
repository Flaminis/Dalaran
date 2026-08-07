use dl_async::AsyncReadAt;

use super::footer_reader::read_dlr_footer_payload;
use crate::dlr::CodecError;

/// A SHA-256 fingerprint of an DLR stream.
//
// NOTE: For an DLR with a footer, this hashes only the encoded footer payload.
// For a legacy DLR without a footer, this hashes the entire stream.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct RrdFingerprint([u8; 32]);

impl RrdFingerprint {
    /// Returns the SHA-256 digest bytes.
    #[inline]
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Computes an DLR fingerprint without reading chunk payloads when possible.
    ///
    /// When a footer is present, the fingerprint is the SHA-256 of its encoded payload.
    /// Otherwise, the entire stream is hashed incrementally.
    pub async fn compute_for_dlr<R: AsyncReadAt>(reader: &R) -> Result<Self, CodecError> {
        use sha2::Digest as _;

        if let Some(payload) = read_dlr_footer_payload(reader).await? {
            return Ok(Self(sha2::Sha256::digest(payload).into()));
        }

        let size = reader.size().await?;
        let mut hasher = sha2::Sha256::new();
        let mut offset = 0u64;
        while offset < size {
            let len = usize::try_from((64 * 1024u64).min(size - offset))?;
            let buffer = reader.read_exact_at(offset, len).await?;
            hasher.update(&buffer);
            offset += len as u64;
        }

        Ok(Self(hasher.finalize().into()))
    }
}

#[cfg(test)]
#[cfg(not(target_arch = "wasm32"))]
mod tests {
    use std::fs::File;

    use sha2::Digest as _;

    use super::*;
    use crate::dlr::test_util::{encode_test_dlr, encode_test_dlr_to_file, make_test_chunks};
    use crate::{Decodable as _, StreamFooter};

    #[test]
    fn test_fingerprint_hashes_footer_payload() {
        let chunks = make_test_chunks(5);
        let (file, _store_id) = encode_test_dlr(&chunks);
        let bytes = std::fs::read(file.path()).unwrap();
        let stream_footer =
            StreamFooter::from_dlr_bytes(&bytes[bytes.len() - StreamFooter::ENCODED_SIZE_BYTES..])
                .unwrap();
        let span = stream_footer.entries[0].dlr_footer_byte_span_from_start_excluding_header;
        let start = usize::try_from(span.start).unwrap();
        let end = usize::try_from(span.start + span.len).unwrap();
        let expected: [u8; 32] = sha2::Sha256::digest(&bytes[start..end]).into();

        let file = File::open(file.path()).unwrap();
        let fingerprint =
            futures::executor::block_on(RrdFingerprint::compute_for_dlr(&file)).unwrap();

        assert_eq!(fingerprint, RrdFingerprint(expected));
    }

    #[test]
    fn test_fingerprint_hashes_legacy_dlr() {
        let file = tempfile::NamedTempFile::new().unwrap();
        let chunks = make_test_chunks(3);
        encode_test_dlr_to_file(file.path(), &chunks, false);
        let bytes = std::fs::read(file.path()).unwrap();
        let expected: [u8; 32] = sha2::Sha256::digest(&bytes).into();

        let file = File::open(file.path()).unwrap();
        let fingerprint =
            futures::executor::block_on(RrdFingerprint::compute_for_dlr(&file)).unwrap();

        assert_eq!(fingerprint, RrdFingerprint(expected));
    }
}
