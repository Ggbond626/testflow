
import json
import zipfile
import uuid
from io import BytesIO
from typing import Dict, List, Optional, Any

class XMindBuilder:
    """
    XMind ZEN (JSON) format builder.
    Handles the creation of .xmind files with proper structure and metadata.
    """
    
    def __init__(self):
        self._content = []
        self._root_topic = None
        
    def create_topic(self, title: str, structure_class: Optional[str] = None) -> Dict[str, Any]:
        """Create a new topic node."""
        topic = {
            "id": str(uuid.uuid4()),
            "title": title,
            "class": "topic"  # Required for some XMind versions
        }
        if structure_class:
            topic["structureClass"] = structure_class
        return topic

    def add_child(self, parent_topic: Dict[str, Any], child_topic: Dict[str, Any]) -> None:
        """Add a child topic to a parent topic."""
        if "children" not in parent_topic:
            parent_topic["children"] = {"attached": []}
        if "attached" not in parent_topic["children"]:
            parent_topic["children"]["attached"] = []
        parent_topic["children"]["attached"].append(child_topic)

    def set_root(self, title: str, structure_class: str = "org.xmind.ui.map.logic.right") -> Dict[str, Any]:
        """Set the root topic of the mind map."""
        self._root_topic = self.create_topic(title, structure_class)
        return self._root_topic

    def build(self) -> BytesIO:
        """Generate the .xmind file (Zip archive) in memory."""
        if not self._root_topic:
            raise ValueError("Root topic not set")
            
        sheet = {
            "id": str(uuid.uuid4()),
            "class": "sheet",
            "title": "画布 1",
            "rootTopic": self._root_topic
        }
        self._content = [sheet]
        
        # Create Zip in memory
        output = BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            # content.json
            zf.writestr("content.json", json.dumps(self._content, ensure_ascii=False))
            
            # metadata.json
            metadata = {
                "creator": {"name": "AutoTestCase", "version": "1.0.0"}
            }
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False))
            
            # manifest.json
            manifest = {
                "file-entries": {
                    "content.json": {},
                    "metadata.json": {}
                }
            }
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
            
        output.seek(0)
        return output
