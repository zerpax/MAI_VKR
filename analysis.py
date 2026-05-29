class OntologyAnalyzer:
    def __init__(self, model):
        self.model = model


    def _get_nodes(self):
        return list(self.model.get_all_nodes())

    def _get_edges(self):
        return list(self.model.get_all_edges())

    def _get_neighbors(self, node_id):
        return self.model.get_neighbors(node_id)

    def _get_type(self, node_id):
        data = self.model.get_node(node_id)
        return data.get("type") if data else None

    def _get_label(self, node_id):
        data = self.model.get_node(node_id)
        return data.get("label") if data else str(node_id)


    def find_isolated_nodes(self):
        """Узлы без связей"""
        isolated = []

        for node_id, _ in self._get_nodes():
            neighbors = self._get_neighbors(node_id)
            if len(neighbors) == 0:
                isolated.append(node_id)

        return isolated

    def find_classes_without_attributes(self):
        """Классы без атрибутов"""
        result = []

        for node_id, data in self._get_nodes():
            if data.get("type") != "class":
                continue

            neighbors = self._get_neighbors(node_id)

            has_attribute = False
            for n in neighbors:
                if self._get_type(n) == "attribute":
                    has_attribute = True
                    break

            if not has_attribute:
                result.append(node_id)

        return result

    def find_classes_without_relations(self):
        """Классы без связей с другими классами"""
        result = []

        for node_id, data in self._get_nodes():
            if data.get("type") != "class":
                continue

            neighbors = self._get_neighbors(node_id)

            has_relation = False
            for n in neighbors:
                if self._get_type(n) == "relation":
                    has_relation = True
                    break

            if not has_relation:
                result.append(node_id)

        return result


    def find_orphan_attributes(self):
        """Атрибуты без класса"""
        result = []

        for node_id, data in self._get_nodes():
            if data.get("type") != "attribute":
                continue

            neighbors = self._get_neighbors(node_id)

            has_class = any(self._get_type(n) == "class" for n in neighbors)

            if not has_class:
                result.append(node_id)

        return result

    def find_invalid_relations(self):
        """Отношения без двух классов"""
        result = []

        for node_id, data in self._get_nodes():
            if data.get("type") != "relation":
                continue

            neighbors = self._get_neighbors(node_id)

            class_count = sum(
                1 for n in neighbors if self._get_type(n) == "class"
            )

            if class_count != 2:
                result.append(node_id)

        return result

    def find_invalid_edges(self):
        """Проверка некорректных связей"""
        invalid = []

        for source, target in self._get_edges():
            t1 = self._get_type(source)
            t2 = self._get_type(target)

            valid = (
                (t1 == "class" and t2 == "attribute") or
                (t2 == "class" and t1 == "attribute") or
                (t1 == "class" and t2 == "relation") or
                (t2 == "class" and t1 == "relation")
            )

            if not valid:
                invalid.append((source, target))

        return invalid


    def get_statistics(self):
        nodes = self._get_nodes()

        classes = 0
        attributes = 0
        relations = 0

        for _, data in nodes:
            t = data.get("type")
            if t == "class":
                classes += 1
            elif t == "attribute":
                attributes += 1
            elif t == "relation":
                relations += 1

        total_edges = len(self._get_edges())

        return {
            "classes": classes,
            "attributes": attributes,
            "relations": relations,
            "edges": total_edges
        }


    def generate_report(self):
        report = {}

        report["isolated_nodes"] = self.find_isolated_nodes()
        report["classes_without_attributes"] = self.find_classes_without_attributes()
        report["classes_without_relations"] = self.find_classes_without_relations()

        report["orphan_attributes"] = self.find_orphan_attributes()
        report["invalid_relations"] = self.find_invalid_relations()
        report["invalid_edges"] = self.find_invalid_edges()

        report["statistics"] = self.get_statistics()

        return report


    def generate_text_report(self):
        report = self.generate_report()

        lines = []

        def format_nodes(title, node_list):
            lines.append(f"\n{title}:")
            if not node_list:
                lines.append("  None")
                return
            lines.append(f" {len(node_list)}")

        lines.append("ONTOLOGY REPORT \n")

        stats = report["statistics"]
        lines.append("STATS:")
        for key, value in stats.items():
            lines.append(f"  {key}: {value}")

        format_nodes("Isolated nodes", report["isolated_nodes"])
        format_nodes("Classes without attributes", report["classes_without_attributes"])
        format_nodes("Classes without relations", report["classes_without_relations"])
        format_nodes("Orphan attributes", report["orphan_attributes"])
        format_nodes("Invalid relations", report["invalid_relations"])
        format_nodes("Invalud edges", report["invalid_edges"])
        


        return "\n".join(lines)