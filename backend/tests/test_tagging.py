from app.services.tagging import TagBatch, TaggedItem, clean_themes, tag_batch, tag_text


def item(number: int, themes: list[str], sentiment: str = "negative") -> TaggedItem:
    return TaggedItem(item_number=number, sentiment=sentiment, themes=themes, summary="Summary.")


def test_clean_themes_drops_unknown_and_duplicates() -> None:
    assert clean_themes("feedback", ["Pace", "pace", "made_up"]) == ["pace"]


def test_clean_themes_falls_back_to_other() -> None:
    assert clean_themes("complaint", ["teleportation"]) == ["other"]


async def test_tagger_output_is_restricted_to_theme_list(fake_models) -> None:
    fake_models["fast"].structured = [TagBatch(items=[item(1, ["hygiene", "pace"])])]
    result = await tag_text("complaint", "Mess 2 ki plates gandi hain")
    assert result.themes == ["hygiene"]
    assert result.sentiment == "negative"


async def test_batch_maps_results_by_number_and_marks_missing(fake_models) -> None:
    fake_models["fast"].structured = [TagBatch(items=[item(2, ["clarity"], "positive")])]
    results = await tag_batch("feedback", ["first", "second"])
    assert results[0] is None
    assert results[1] is not None and results[1].themes == ["clarity"]
