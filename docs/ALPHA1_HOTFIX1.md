# Version 1.1 Alpha 1 Hotfix 1

This hotfix corrects the Activity Log crash in the graphical application.

## Fixed

The PySide6 text cursor API is now used correctly:

```python
self.log.moveCursor(QTextCursor.MoveOperation.End)
```

This replaces the invalid instance attribute access that caused:

```text
AttributeError: 'PySide6.QtGui.QTextCursor' object has no attribute 'End'
```
