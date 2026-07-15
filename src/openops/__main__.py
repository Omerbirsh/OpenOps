"""Allow ``python -m openops`` to invoke the package entry point."""

from openops.cli import main

raise SystemExit(main())
