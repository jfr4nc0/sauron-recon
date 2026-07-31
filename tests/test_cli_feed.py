import json

from sauron_recon.entrypoints.cli import main


def test_cli_runs_local_feed_without_live_firecrawl(tmp_path, capsys):
    feed = tmp_path / "listings.json"
    feed.write_text(json.dumps([{
        "url": "https://example.org/local-1",
        "title": "Local Palermo",
        "operation": "alquiler",
        "zone": "Palermo",
        "price": "USD 1000",
        "area_m2": "80",
    }]), encoding="utf-8")

    assert main(["search", "--criteria", '{"operation":"rent","zones":["Palermo"]}', "--feed", str(feed), "--dry-run"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "offline"
    assert output["listings"][0]["source"] == "feed:listings"
