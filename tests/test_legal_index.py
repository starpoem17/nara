"""Behavior checks through the index-building and search interfaces."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np

from nara.retrieval.index import SourceText, build_index, passages_for, read_sources
from nara.retrieval.search import LegalRetriever


class CharacterTokenizer:
    def __call__(self, text, *, add_special_tokens=True, **kwargs):
        result = {"input_ids": list(range(len(text) + (2 if add_special_tokens else 0)))}
        if kwargs.get("return_offsets_mapping"):
            result["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return result


class TestEncoder:
    signature = {"model": "test", "dimension": 3}
    tokenizer = CharacterTokenizer()

    def encode(self, texts):
        return np.array([[text.count("입찰"), text.count("소프트웨어"), 0.01]
                         for text in texts], dtype=np.float32)


HWPX = """<section xmlns:hp="urn:test">
<hp:p><hp:run><hp:t>고시 본문</hp:t></hp:run></hp:p>
<hp:p><hp:run><hp:tbl>
<hp:tr>
 <hp:tc header="1"><hp:subList><hp:p><hp:run><hp:t>분류</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
 <hp:tc header="1"><hp:subList><hp:p><hp:run><hp:t>품목</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="1" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
</hp:tr>
<hp:tr>
 <hp:tc header="0"><hp:subList><hp:p><hp:run><hp:t>공통분류</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="1"/><hp:cellSpan colSpan="1" rowSpan="2"/></hp:tc>
 <hp:tc header="0"><hp:subList><hp:p><hp:run><hp:t>품목A</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="1" rowAddr="1"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
</hp:tr>
<hp:tr>
 <hp:tc header="0"><hp:subList><hp:p><hp:run><hp:t>품목B</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="1" rowAddr="2"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
</hp:tr>
</hp:tbl></hp:run></hp:p></section>"""


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        (self.corpus / "입찰법.txt").write_text("제1조(입찰) 입찰 입찰 자격.\n")
        (self.corpus / "소프트웨어법.txt").write_text("제1조(참여) 소프트웨어 소프트웨어 사업.\n")
        self.encoder = TestEncoder()

    def build(self):
        output = self.root / "index"
        manifest = build_index(self.corpus, output, self.encoder,
                               chunk_tokens=128, overlap_tokens=8)
        return output, manifest

    def test_search_preserves_ids_and_returns_the_right_sources(self):
        output, _ = self.build()
        retriever = LegalRetriever(output, self.encoder)
        hits = retriever.search({"second-task": "소프트웨어", "first-task": "입찰"}, top_k=1)
        self.assertEqual(list(hits), ["second-task", "first-task"])
        self.assertEqual(hits["second-task"][0].source, "소프트웨어법.txt")
        self.assertEqual(hits["first-task"][0].source, "입찰법.txt")
        self.assertIn("자격", hits["first-task"][0].text)

    def test_empty_queries_and_invalid_input(self):
        output, _ = self.build()
        retriever = LegalRetriever(output, self.encoder)
        self.assertEqual(retriever.search({}), {})
        for queries, top_k in [({"task": ""}, 1), ({"": "입찰"}, 1), ({"task": "입찰"}, 0)]:
            with self.assertRaises(ValueError):
                retriever.search(queries, top_k=top_k)

    def test_incompatible_encoder_and_corrupt_index_are_rejected(self):
        output, _ = self.build()
        other = TestEncoder()
        other.signature = {"model": "different", "dimension": 3}
        with self.assertRaisesRegex(ValueError, "incompatible"):
            LegalRetriever(output, other)
        with (output / "passages.jsonl").open("a") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            LegalRetriever(output, self.encoder)

    def test_existing_index_is_not_overwritten(self):
        output, _ = self.build()
        original = (output / "manifest.json").read_bytes()
        with self.assertRaises(FileExistsError):
            build_index(self.corpus, output, self.encoder)
        self.assertEqual((output / "manifest.json").read_bytes(), original)

    def test_passage_splitting_preserves_text_and_limits_with_overlap(self):
        text = "법령 머리말\n제1조(목적) " + "긴 조문과 예외 사항.\n" * 100 + "제2조(끝) 마지막 단서."
        document = SourceText("법령.txt", "text", "법령 제목", text)
        passages = list(passages_for(document, self.encoder.tokenizer,
                                    chunk_tokens=128, overlap_tokens=8))
        covered = set()
        for passage in passages:
            start, end = passage["char_start"], passage["char_end"]
            self.assertEqual(passage["text"], text[start:end])
            self.assertLessEqual(
                len(self.encoder.tokenizer(passage["embedding_text"])["input_ids"]), 128,
            )
            covered.update(range(start, end))
        self.assertTrue(all(i in covered for i, c in enumerate(text) if not c.isspace()))
        self.assertGreater(len(passages), 2)
        self.assertEqual(len({p["id"] for p in passages}), len(passages))
        changed = list(passages_for(replace(document, locator="other"), self.encoder.tokenizer,
                                    chunk_tokens=128, overlap_tokens=8))
        self.assertTrue({p["id"] for p in passages}.isdisjoint(p["id"] for p in changed))

    def test_csv_codes_and_hwpx_merged_cells_keep_their_context(self):
        (self.corpus / "품목.csv").write_text("번호,품목,특이사항\n00123,제품,예외 있음\n")
        with zipfile.ZipFile(self.corpus / "고시.hwpx", "w") as archive:
            archive.writestr("Contents/section0.xml", HWPX)
        documents, sources = read_sources(self.corpus)
        self.assertEqual(len(sources), 4)
        csv_document = next(d for d in documents if d.source.endswith(".csv"))
        self.assertIn("번호: 00123", csv_document.text)
        self.assertIn("특이사항: 예외 있음", csv_document.text)
        hwpx = [d for d in documents if d.source.endswith(".hwpx")]
        self.assertEqual(len(hwpx), 3)
        self.assertEqual(hwpx[0].text.count("고시 본문"), 1)
        self.assertNotIn("품목A", hwpx[0].text)
        self.assertIn("분류: 공통분류", hwpx[1].text)
        self.assertIn("분류: 공통분류", hwpx[2].text)
        self.assertIn("품목: 품목B", hwpx[2].text)

    def test_duplicate_text_is_not_returned_twice(self):
        (self.corpus / "복제.txt").write_text("제1조(입찰) 입찰 입찰 자격.\n")
        output, manifest = self.build()
        self.assertEqual(manifest["duplicate_text_count"], 1)
        hits = LegalRetriever(output, self.encoder).search({"query": "입찰"}, top_k=10)["query"]
        self.assertEqual(len(hits), 2)

    def test_empty_source_is_not_silently_omitted(self):
        (self.corpus / "empty.txt").write_text("")
        with self.assertRaisesRegex(ValueError, "no extractable text"):
            read_sources(self.corpus)

    def test_unknown_sources_fail_instead_of_being_skipped(self):
        (self.corpus / "unhandled.pdf").write_bytes(b"not a text file")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            read_sources(self.corpus)


if __name__ == "__main__":
    unittest.main()
