Process a book through the pipeline.

## Arguments
- Book ID: $ARGUMENTS (e.g. `chandrakanta`, `feluda`, `byomkesh`)

## Instructions

Run the book processing pipeline for the given book ID. The pipeline stages are:
`ocr → translate → chapters → json → annotations → images → characters → heroes`

1. First check the current status of the book:
   ```
   uv run python -m pipeline.run --status
   ```

2. Look at which stages are already complete for this book.

3. Run the pipeline starting from the first incomplete stage:
   ```
   uv run python -m pipeline.run --book <BOOK_ID> --from <FIRST_INCOMPLETE_STAGE>
   ```
   If no stages are complete, run the full pipeline:
   ```
   uv run python -m pipeline.run --book <BOOK_ID>
   ```

4. **IMPORTANT**: Image generation stages (`images`, `characters`, `heroes`) should be run in parallel in the background using `run_in_background=true`. Never block on image generation. Run them like:
   ```
   uv run python -m pipeline.run --book <BOOK_ID> --stage images
   uv run python -m pipeline.run --book <BOOK_ID> --stage characters
   uv run python -m pipeline.run --book <BOOK_ID> --stage heroes
   ```

5. After all stages complete, verify the output:
   - Check that `web/public/data/books/<BOOK_ID>/chapters.json` exists
   - Check that `web/public/data/books/<BOOK_ID>/annotations.json` exists
   - Check that images exist in `web/public/data/images/`

6. If adding a **new book**, first add a `BookConfig` entry in `pipeline/config.py`, then run the pipeline.

## Notes
- Always use `uv run` to execute pipeline commands
- The pipeline is checkpoint-based and resumable
- If a stage fails, fix the issue and re-run that specific stage with `--stage`
- Use `--force` flag to re-run a stage that's already complete
