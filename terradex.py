from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Tree, ListView, ListItem, Label, Markdown, Input
import json

# Load the Terraform provider schema from a JSON file named schema.json
# Note: This file is generated at runtime by OpenTofu using 'tofu providers schema -json'
def load_schema():
    with open("/tmp/schema.json", "r") as file:
        data = json.load(file)
    return data.get("provider_schemas", {})  # Extract only provider schemas

class TerradexApp(App):
    """A Textual app with a 3x2 Grid layout for provider navigation, attributes, and details, including search functionality with styled border titles using Textual's theming."""
    
    CSS = """
    #app-layout {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 2fr 1fr 3fr;
    }
    #provider-nav {
        border: solid darkgray;  /* Grey border for the Tree (using ANSI color name) */
        background: $panel;      /* Use Textual's panel background color */
        color: $text;            /* Use Textual's default text color */
    }
    #search-input {
        height: 3;       /* Fixed height for the search input (adjust as needed) */
        border: solid darkgray;  /* Grey border for the Input (using ANSI color name) */
        background: $surface;    /* Use Textual's surface background color for dark mode compatibility */
        color: white;            /* White text for maximum contrast in dark mode */
    }
    #search-input:focus {
        border: solid yellow;  /* Highlight on focus for better visibility */
        outline: none;       /* Remove default outline if needed */
        color: white;
    }
    #attribute-list {
        height: 100%;             /* Span both rows */
        border: solid darkgray;   /* Grey border for the ListView (using ANSI color name) */
        background: $panel;       /* Use Textual's panel background color */
        color: $text;             /* Use Textual's default text color */
    }
    #attribute-details {
        height: 100%;             /* Span both rows */
        border: solid darkgray;   /* Grey border for the Markdown (using ANSI color name) */
        background: $panel;       /* Use Textual's panel background color */
        color: $text;             /* Use Textual's default text color */
        overflow-x: hidden;       /* Prevent horizontal overflow */
    }
    """

    def __init__(self):
        super().__init__()
        self.schema = load_schema()
        self.last_selected_node = None  # Store the last selected node in the Tree
        self.original_tree_state = None  # Store the original Tree state for resetting

    def on_mount(self) -> None:
        """Populate the Tree widget with provider schemas and their child nodes, storing the original state, and set border titles."""
        provider_nav = self.query_one("#provider-nav", Tree)
        search_input = self.query_one("#search-input", Input)
        attribute_list = self.query_one("#attribute-list", ListView)
        attribute_details = self.query_one("#attribute-details", Markdown)

        # Set border titles on widgets
        provider_nav.border_title = "schemas"
        search_input.border_title = "search"
        attribute_list.border_title = "attributes"
        attribute_details.border_title = "details"

        root = provider_nav.root
        root.expand()

        self.original_tree_state = []  # Store the original provider names for resetting
        for provider, provider_data in self.schema.items():
            provider_node = root.add(provider)
            self.original_tree_state.append(provider)  # Store the provider name (string) instead of the TreeNode

            # Add resources under provider
            resources = provider_data.get("resource_schemas", {})
            if resources:
                resource_node = provider_node.add("Resources")
                for resource in resources:
                    resource_node.add_leaf(resource)

            # Add data sources under provider
            data_sources = provider_data.get("data_source_schemas", {})
            if data_sources:
                data_source_node = provider_node.add("Data Sources")
                for data_source in data_sources:
                    data_source_node.add_leaf(data_source)

            # Add functions under provider
            functions = provider_data.get("functions", {})
            if functions:
                function_node = provider_node.add("Functions")
                for function_name in functions:
                    function_node.add_leaf(function_name)

        provider_nav.focus()

    def compose(self) -> ComposeResult:
        """Set up the initial 3x2 Grid layout using Textual containers, with border titles on widgets."""
        with Container(id="app-layout"):
            with Vertical():
                yield Tree("Providers", id="provider-nav")
                yield Input(placeholder="Search providers, resources, data sources, and functions...", id="search-input")
            yield ListView(id="attribute-list")
            yield Markdown("", id="attribute-details")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle selection in the Tree widget to update the ListView with attributes or function keys and render all markdown in attribute-details, resetting scroll to top."""
        selected_node = event.node
        selected_label = str(selected_node.label)
        parent_node = selected_node.parent
        grandparent_node = parent_node.parent if parent_node else None  # Get the provider (grandparent)

        print(f"Selected node: {selected_label}, Parent node: {parent_node.label if parent_node else 'None'}, Grandparent node: {grandparent_node.label if grandparent_node else 'None'}")

        self.last_selected_node = selected_node  # Store the last selected node

        attribute_list = self.query_one("#attribute-list", ListView)
        markdown_widget = self.query_one("#attribute-details", Markdown)

        # Clear the ListView to start fresh
        attribute_list.clear()

        if grandparent_node and str(grandparent_node.label) in self.schema:
            provider = str(grandparent_node.label)
            provider_data = self.schema[provider]
            print(f"Provider data found for: {provider}")

            # Render all markdown for the selected item and populate the ListView with keys
            if parent_node and str(parent_node.label) == "Resources" and selected_label in provider_data.get("resource_schemas", {}):
                block_data = provider_data["resource_schemas"][selected_label]["block"]
                print(f"Resource schema found: {selected_label}, Attributes: {block_data.get('attributes', {})}")
                self._populate_attributes(attribute_list, block_data.get("attributes", {}))
                markdown_content = self._get_all_markdown_for_item(provider_data, selected_label, "resource")
                markdown_widget.update(markdown_content)
            elif parent_node and str(parent_node.label) == "Data Sources" and selected_label in provider_data.get("data_source_schemas", {}):
                block_data = provider_data["data_source_schemas"][selected_label]["block"]
                print(f"Data source schema found: {selected_label}, Attributes: {block_data.get('attributes', {})}")
                self._populate_attributes(attribute_list, block_data.get("attributes", {}))
                markdown_content = self._get_all_markdown_for_item(provider_data, selected_label, "data_source")
                markdown_widget.update(markdown_content)
            elif parent_node and str(parent_node.label) == "Functions":
                if selected_label in provider_data.get("functions", {}):
                    function_data = provider_data["functions"][selected_label]
                    print(f"Function found: {selected_label}, Keys: {list(function_data.keys())}")
                    self._populate_attributes(attribute_list, {selected_label: function_data})  # Use the function name as the key
                    markdown_content = self._get_all_markdown_for_item(provider_data, selected_label, "function")
                    markdown_widget.update(markdown_content)
                else:
                    print(f"Function category selected: {selected_label}, populating all function keys")
                    self._populate_attributes(attribute_list, provider_data.get("functions", {}))
                    markdown_content = self._get_all_markdown_for_functions(provider_data)
                    markdown_widget.update(markdown_content)
            else:
                print(f"No valid resource, data source, or function found for: {selected_label}")
                markdown_widget.update("# No Details Available\n\nSelect a valid resource, data source, or function to view details.")
        else:
            print(f"No provider found for: {selected_label}")
            markdown_widget.update("# No Details Available\n\nSelect a valid resource, data source, or function to view details.")

        # Reset the scroll position of the Markdown widget to the top
        markdown_widget.scroll_y = 0  # Set vertical scroll position to 0 (top)

    def _populate_attributes(self, attribute_list: ListView, attributes: dict) -> None:
        """Populate the ListView with attribute or function names from the block or function data."""
        for attr_name in attributes.keys():
            attribute_list.append(ListItem(Label(attr_name)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection in the ListView to navigate to the specific markdown header in attribute-details."""
        selected_item = event.item
        # Safely get the text from the Label inside the ListItem
        label = selected_item.query_one(Label)
        attribute_name = str(label.renderable) if label.renderable else str(label)
        parent_node = self.last_selected_node  # Use the last selected node from the Tree

        # Traverse up to find the provider (grandparent of the selected node)
        provider_node = parent_node
        while provider_node and provider_node.parent:
            if not provider_node.parent.parent:  # If this is the root-level provider
                provider = str(provider_node.label)
                break
            provider_node = provider_node.parent
        else:
            provider = None

        selected_label = str(parent_node.label) if parent_node else None

        print(f"ListView Selected - Attribute/Function: {attribute_name}, Provider: {provider}, Selected Label: {selected_label}")

        if provider and selected_label:
            markdown_widget = self.query_one("#attribute-details", Markdown)
            # Use Textual's default anchor format: lowercase with hyphens, no underscores
            anchor = f"{attribute_name.replace(' ', '-').lower()}"
            print(f"Attempting to navigate to anchor: {anchor}")
            try:
                markdown_widget.goto_anchor(anchor)  # Navigate to the corresponding header in the markdown
                print(f"Successfully navigated to anchor: {anchor}")
            except Exception as e:
                print(f"Failed to navigate to anchor {anchor}: {e}")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle highlighting (hover/focus) in the ListView to navigate to the specific markdown header in attribute-details."""
        highlighted_item = event.item
        print(f"Highlighted item: {highlighted_item}")  # Debug print to track the highlighted item

        if highlighted_item is None:
            print("No highlighted item, skipping update")
            return  # Skip processing if no item is highlighted

        label = highlighted_item.query_one(Label)
        attribute_name = str(label.renderable) if label.renderable else str(label)
        parent_node = self.last_selected_node  # Use the last selected node from the Tree

        # Traverse up to find the provider (grandparent of the highlighted node)
        provider_node = parent_node
        while provider_node and provider_node.parent:
            if not provider_node.parent.parent:  # If this is the root-level provider
                provider = str(provider_node.label)
                break
            provider_node = provider_node.parent
        else:
            provider = None

        selected_label = str(parent_node.label) if parent_node else None

        print(f"ListView Highlighted - Attribute/Function: {attribute_name}, Provider: {provider}, Selected Label: {selected_label}")

        if provider and selected_label:
            markdown_widget = self.query_one("#attribute-details", Markdown)
            # Use Textual's default anchor format: lowercase with hyphens, no underscores
            anchor = f"{attribute_name.replace(' ', '-').lower()}"
            print(f"Attempting to navigate to anchor: {anchor}")
            try:
                markdown_widget.goto_anchor(anchor)  # Navigate to the corresponding header in the markdown
                print(f"Successfully navigated to anchor: {anchor}")
            except Exception as e:
                print(f"Failed to navigate to anchor {anchor}: {e}")

    def _get_all_markdown_for_item(self, provider_data: dict, item_label: str, item_type: str) -> str:
        """Generate a single markdown document for all attributes of a resource, data source, or function."""
        if item_type == "resource" and item_label in provider_data.get("resource_schemas", {}):
            block_data = provider_data["resource_schemas"][item_label]["block"]
            attributes = block_data.get("attributes", {})
            markdown_content = f"# {item_label}\n\n"
            for attr_name, attr_info in attributes.items():
                description = attr_info.get("description", "No description available.")
                markdown_content += f"## {attr_name}\n\n{description}\n\n"
                # Create a markdown table for other fields, excluding description and description_kind
                other_fields = {k: v for k, v in attr_info.items() if k not in ["description", "description_kind"]}
                if other_fields:
                    markdown_content += "| Field | Value |\n|-------|-------|\n"
                    for field, value in other_fields.items():
                        if isinstance(value, (list, dict)):
                            value = str(value)  # Convert complex types to string for display
                        markdown_content += f"| {field} | {value} |\n"  # Removed extra parenthesis
                    markdown_content += "\n"
            return markdown_content
        elif item_type == "data_source" and item_label in provider_data.get("data_source_schemas", {}):
            block_data = provider_data["data_source_schemas"][item_label]["block"]
            attributes = block_data.get("attributes", {})
            markdown_content = f"# {item_label}\n\n"
            for attr_name, attr_info in attributes.items():
                description = attr_info.get("description", "No description available.")
                markdown_content += f"## {attr_name}\n\n{description}\n\n"
                # Create a markdown table for other fields, excluding description and description_kind
                other_fields = {k: v for k, v in attr_info.items() if k not in ["description", "description_kind"]}
                if other_fields:
                    markdown_content += "| Field | Value |\n|-------|-------|\n"
                    for field, value in other_fields.items():
                        if isinstance(value, (list, dict)):
                            value = str(value)  # Convert complex types to string for display
                        markdown_content += f"| {field} | {value} |\n"  # Removed extra parenthesis
                    markdown_content += "\n"
            return markdown_content
        elif item_type == "function" and item_label in provider_data.get("functions", {}):
            function_data = provider_data["functions"][item_label]
            summary = function_data.get("summary", "No description available.")
            description = function_data.get("description", "No description available.")
            return_type = function_data.get("return_type", "No return type available.")
            parameters = function_data.get("parameters", [])

            # Create a single markdown document for the function
            markdown_content = f"# {item_label}\n\n## Summary\n{summary}\n\n## Description\n{description}\n\n## Return Type\n{return_type}\n\n"

            # Render parameters as a markdown table if there are any
            if parameters:
                markdown_content += "## Parameters\n| Name | Type | Description |\n|------|------|-------------|\n"
                for param in parameters:
                    name = param.get("name", "N/A")
                    param_type = param.get("type", "N/A")
                    param_desc = param.get("description", "No description available.")
                    markdown_content += f"| {name} | {param_type} | {param_desc} |\n"
            else:
                markdown_content += "## Parameters\nNo parameters available.\n"

            return markdown_content
        else:
            return "# No Details Available\n\nSelect a valid resource, data source, or function to view details."

    def _get_all_markdown_for_functions(self, provider_data: dict) -> str:
        """Generate a single markdown document for all functions of a provider."""
        functions = provider_data.get("functions", {})
        markdown_content = "# Functions\n\n"
        for function_name, function_data in functions.items():
            summary = function_data.get("summary", "No summary available.")
            description = function_data.get("description", "No description available.")
            return_type = function_data.get("return_type", "No return type available.")
            parameters = function_data.get("parameters", [])

            markdown_content += f"## {function_name}\n\n"
            markdown_content += f"### Summary\n{summary}\n\n### Description\n{description}\n\n### Return Type\n{return_type}\n\n"

            # Render parameters as a markdown table if there are any
            if parameters:
                markdown_content += "### Parameters\n| Name | Type | Description |\n|------|------|-------------|\n"
                for param in parameters:
                    name = param.get("name", "N/A")
                    param_type = param.get("type", "N/A")
                    param_desc = param.get("description", "No description available.")
                    markdown_content += f"| {name} | {param_type} | {param_desc} |\n"
            else:
                markdown_content += "### Parameters\nNo parameters available.\n"
            markdown_content += "\n"
        return markdown_content

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes to dynamically filter the Tree with matching providers, resources, data sources, and functions, ensuring unique provider and category nodes, and expanding parent nodes of matches."""
        search_query = event.value.lower().strip()
        provider_nav = self.query_one("#provider-nav", Tree)
        provider_nav.clear()

        if not search_query:
            # Reset the Tree to its original state
            if self.original_tree_state:
                for provider in self.original_tree_state:
                    provider_node = provider_nav.root.add(provider)
                    # Rebuild the children for each provider from the schema
                    provider_data = self.schema[provider]
                    # Add resources
                    resources = provider_data.get("resource_schemas", {})
                    if resources:
                        resource_node = provider_node.add("Resources")
                        for resource in resources:
                            resource_node.add_leaf(resource)
                    # Add data sources
                    data_sources = provider_data.get("data_source_schemas", {})
                    if data_sources:
                        data_source_node = provider_node.add("Data Sources")
                        for data_source in data_sources:
                            data_source_node.add_leaf(data_source)
                    # Add functions
                    functions = provider_data.get("functions", {})
                    if functions:
                        function_node = provider_node.add("Functions")
                        for function_name in functions:
                            function_node.add_leaf(function_name)
                provider_nav.root.expand()
            return

        # Use a nested dictionary to track unique providers, their categories, and matching child nodes
        provider_matches = {}
        for provider, provider_data in self.schema.items():
            category_matches = {
                "Resources": [],
                "Data Sources": [],
                "Functions": []
            }
            # Check providers
            if search_query in provider.lower():
                category_matches["Provider"] = [("Provider", provider, None)]

            # Check resources
            for resource in provider_data.get("resource_schemas", {}).keys():
                if search_query in resource.lower():
                    category_matches["Resources"].append(("Resource", resource, provider_data["resource_schemas"][resource]["block"]))

            # Check data sources
            for data_source in provider_data.get("data_source_schemas", {}).keys():
                if search_query in data_source.lower():
                    category_matches["Data Sources"].append(("Data Source", data_source, provider_data["data_source_schemas"][data_source]["block"]))

            # Check functions
            for function in provider_data.get("functions", {}).keys():
                if search_query in function.lower():
                    category_matches["Functions"].append(("Function", function, {"description": provider_data["functions"][function]["description"]}))

            # Only include the provider if there are any matches
            has_matches = any(category_matches.values())
            if has_matches:
                provider_matches[provider] = category_matches

        # Build the Tree with unique providers and their categories, ensuring no duplicates
        for provider, categories in provider_matches.items():
            provider_node = provider_nav.root.add(provider)
            for category, matches in categories.items():
                if not matches or category == "Provider":
                    continue
                category_node = provider_node.add(category)
                for match_type, match_label, match_data in matches:
                    category_node.add_leaf(match_label)

        provider_nav.root.expand()

        # Recursively expand all nodes with children
        def expand_nodes(node):
            if node.children:
                node.expand()
                for child in node.children:
                    expand_nodes(child)

        expand_nodes(provider_nav.root)

    def _clear_details(self) -> None:
        """Clear the Markdown widget when no attributes are selected."""
        markdown_widget = self.query_one("#attribute-details", Markdown)
        markdown_widget.update("# No Details Available\n\nSelect a valid resource, data source, or function to view details.")

if __name__ == "__main__":
    app = TerradexApp()
    app.run()
