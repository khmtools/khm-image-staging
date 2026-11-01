# Sunday product image enhancement — runbook (khmtools.com.ph)

Goal (Sir Kim): every product main image at least 1000 x 1000 px, not pixelated. Images already >= 1000 px are left alone.

## Files here
- `work/todo.json` — main images still under 1000 px: `[cdn_url, width, height, google_clicks]`, ordered by Google clicks (highest first). Built from the Merchant Center export of 30 Oct 2026.
- `work/done_filenames.json` — CDN filenames already replaced (or deliberately skipped, see `work/skipped.json`).
- `work/batch_enhance.py` — downloads + FSRCNN x4 upscale + 1000x1000 white square + light sharpen. Usage: `SR_MODEL=/home/claude/models/FSRCNN_x4.pb python3 batch_enhance.py items.json OUTDIR` (items = list of [url, ...]). Skips files already in OUTDIR.

## Each run (cap: about 1,500 images)
1. **Confirm the store**: Shopify `{ shop { primaryDomain { host } } }` must be `khmtools.com.ph`. If not, STOP, change nothing, and tell Sir Kim the connector is on another store.
2. Attach + clone this repo (`add_repo` khmtools/khm-image-staging, access push; `git clone --depth 1`). Download the model: `curl -sSL -o /home/claude/models/FSRCNN_x4.pb https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x4.pb`.
3. Take the next ~1,500 entries of todo.json whose filename (`url.split('?')[0].rsplit('/',1)[1]`) is not in done_filenames.json.
4. Enhance them (run in the background in chunks of ~300; long foreground commands get cut off; the script skips finished files).
5. Map filename → MediaImage ID with aliased queries, 60 per call:
   `{a0:files(first:2,query:"filename:'<name>'"){nodes{id}} a1:...}` (escape `'` and `"`).
   Exactly 1 node → use it. 0 or 2 nodes → skip that image (add to skipped.json). Filename search is the only safe cheap lookup; never guess.
6. Rename each enhanced file to `r<YYYYMMDD>/<mediaId>.jpg`, commit, `git fetch origin main && git rebase origin/main`, push.
7. Replace in place, 50 per call:
   `mutation { fileUpdate(files:[{id:"gid://shopify/MediaImage/<id>",originalSource:"https://raw.githubusercontent.com/khmtools/khm-image-staging/main/r<YYYYMMDD>/<id>.jpg"}, ...]) { files { id fileStatus } userErrors { field message code } } }`
   Only change the image file — never titles, handles, URLs, alt text or anything else (Google Ads flag: no URL changes).
8. Spot-check 3 replaced images: query `image { width height url }` (expect 1000x1000) and look at one.
9. Append the replaced + skipped filenames to done_filenames.json / skipped.json, `git rm -r` the r<date> folder (Shopify already copied the files), commit, push.
10. Update the Progress section of project doc `claude/image-enhance/rollout.md`.
11. Short message to Sir Kim: images enhanced this run, total done vs remaining, any skips, and that nothing else was changed.
