.PHONY: dev app build clean

# ── Dev: Flask in browser with auto-reload on :5001 ──
dev:
	@echo "Starting Flask dev server with auto-reload..."
	.venv/bin/python run.py --port 5001 --debug

# ── App: launch Electrobun desktop window (QA/testing) ──
app:
	cd desktop && bun run start

# ── Build: production .app bundle ──
build:
	cd desktop && bun run build:prod
	@echo ""
	@echo "Build complete. App bundle at:"
	@ls -d desktop/build/prod-*/*.app 2>/dev/null || echo "  (check desktop/build/)"

# ── Clean build artifacts ──
clean:
	rm -rf desktop/build
