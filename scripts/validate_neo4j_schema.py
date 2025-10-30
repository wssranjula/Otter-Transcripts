"""
Neo4j Schema Validator for ReAct Agent
Checks if your schema follows best practices for optimal agent performance
"""

import json
import ssl
import certifi
from neo4j import GraphDatabase
from typing import Dict, List, Tuple


class Neo4jSchemaValidator:
    """Validate Neo4j schema for ReAct agent compatibility"""
    
    def __init__(self, uri: str, user: str, password: str):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(uri, auth=(user, password), ssl_context=ssl_context)
        self.issues = []
        self.recommendations = []
        
    def close(self):
        self.driver.close()
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks
        
        Returns:
            (is_valid, issues, recommendations)
        """
        print("="*70)
        print("🔍 NEO4J SCHEMA VALIDATION FOR REACT AGENT")
        print("="*70)
        print()
        
        # Run checks
        self._check_node_labels()
        self._check_property_consistency()
        self._check_temporal_properties()
        self._check_indexes()
        self._check_constraints()
        self._check_relationships()
        self._check_full_text_indexes()
        self._check_entity_normalization()
        
        # Results
        print("\n" + "="*70)
        print("📊 VALIDATION RESULTS")
        print("="*70)
        
        is_valid = len(self.issues) == 0
        
        if is_valid:
            print("\n✅ PASSED - Your schema is agent-friendly!")
        else:
            print(f"\n⚠️  ISSUES FOUND - {len(self.issues)} problem(s) detected")
            print("\n🔴 Issues:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.recommendations:
            print(f"\n💡 Recommendations ({len(self.recommendations)}):")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*70)
        
        return is_valid, self.issues, self.recommendations
    
    def _check_node_labels(self):
        """Check for clear, descriptive node labels"""
        print("\n1️⃣  Checking node labels...")
        
        with self.driver.session() as session:
            result = session.run("""
                CALL db.labels() YIELD label
                RETURN label
            """)
            labels = [record['label'] for record in result]
        
        if not labels:
            self.issues.append("No node labels found - database is empty")
            return
        
        print(f"   Found {len(labels)} node types: {', '.join(labels)}")
        
        # Check for generic labels
        generic_labels = ['Node', 'Thing', 'Item', 'Object', 'Data']
        found_generic = [l for l in labels if l in generic_labels]
        if found_generic:
            self.issues.append(f"Generic labels found: {found_generic}. Use specific labels like 'Meeting', 'Document'")
        else:
            print("   ✓ All labels are specific and descriptive")
    
    def _check_property_consistency(self):
        """Check for consistent property naming across types"""
        print("\n2️⃣  Checking property consistency...")
        
        with self.driver.session() as session:
            # Check common properties
            common_props = ['title', 'date', 'id', 'content', 'text']
            
            for prop in common_props:
                result = session.run(f"""
                    MATCH (n)
                    WHERE n.`{prop}` IS NOT NULL
                    RETURN DISTINCT labels(n)[0] as label
                """)
                labels_with_prop = [record['label'] for record in result]
                
                if len(labels_with_prop) > 1:
                    print(f"   ✓ Property '{prop}' used consistently across: {', '.join(labels_with_prop)}")
    
    def _check_temporal_properties(self):
        """Check for date/timestamp properties"""
        print("\n3️⃣  Checking temporal properties...")
        
        with self.driver.session() as session:
            # Check for date fields
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as total,
                       count(n.date) as with_date,
                       count(n.timestamp) as with_timestamp
            """)
            
            for record in result:
                label = record['label']
                total = record['total']
                with_date = record['with_date']
                with_timestamp = record['with_timestamp']
                
                if with_date == 0 and with_timestamp == 0:
                    self.issues.append(f"Node type '{label}' has no temporal properties (date/timestamp)")
                elif with_date < total:
                    self.recommendations.append(f"Only {with_date}/{total} '{label}' nodes have dates")
                else:
                    print(f"   ✓ All '{label}' nodes have temporal properties")
    
    def _check_indexes(self):
        """Check for performance indexes"""
        print("\n4️⃣  Checking indexes...")
        
        with self.driver.session() as session:
            result = session.run("SHOW INDEXES")
            indexes = list(result)
        
        if not indexes:
            self.issues.append("No indexes found - add indexes for better performance")
        else:
            print(f"   ✓ Found {len(indexes)} indexes")
            
            # Check for common index types
            indexed_props = set()
            for idx in indexes:
                if 'properties' in idx:
                    indexed_props.update(idx['properties'])
            
            recommended_indexes = ['id', 'date', 'timestamp', 'name']
            missing = [p for p in recommended_indexes if p not in indexed_props]
            
            if missing:
                self.recommendations.append(f"Consider indexing: {', '.join(missing)}")
    
    def _check_constraints(self):
        """Check for constraints"""
        print("\n5️⃣  Checking constraints...")
        
        with self.driver.session() as session:
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
        
        if not constraints:
            self.recommendations.append("No constraints found - add UNIQUE constraints on ID fields")
        else:
            print(f"   ✓ Found {len(constraints)} constraints")
    
    def _check_relationships(self):
        """Check for meaningful relationships"""
        print("\n6️⃣  Checking relationships...")
        
        with self.driver.session() as session:
            result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN relationshipType
            """)
            rel_types = [record['relationshipType'] for record in result]
        
        if not rel_types:
            self.issues.append("No relationships found - connect your nodes!")
            return
        
        print(f"   ✓ Found {len(rel_types)} relationship types: {', '.join(rel_types)}")
        
        # Check for generic relationships
        generic_rels = ['HAS', 'RELATED_TO', 'CONNECTED', 'LINKED']
        found_generic = [r for r in rel_types if r in generic_rels]
        if found_generic:
            self.recommendations.append(f"Generic relationships found: {found_generic}. Use specific ones like 'CONTAINS', 'SPOKE_IN'")
    
    def _check_full_text_indexes(self):
        """Check for full-text search indexes"""
        print("\n7️⃣  Checking full-text indexes...")
        
        with self.driver.session() as session:
            result = session.run("""
                SHOW INDEXES
                YIELD name, type
                WHERE type = 'FULLTEXT'
                RETURN name
            """)
            fulltext_indexes = list(result)
        
        if not fulltext_indexes:
            self.issues.append("No full-text indexes found - add them for text search!")
            self.recommendations.append("Create: CREATE FULLTEXT INDEX chunk_text_index FOR (c:Chunk) ON EACH [c.text]")
        else:
            print(f"   ✓ Found {len(fulltext_indexes)} full-text indexes")
    
    def _check_entity_normalization(self):
        """Check for duplicate entities"""
        print("\n8️⃣  Checking entity normalization...")
        
        with self.driver.session() as session:
            # Check for Person nodes with similar names
            result = session.run("""
                MATCH (p:Person)
                WITH p.name as name, count(*) as count
                WHERE count > 1
                RETURN name, count
            """)
            duplicates = list(result)
            
            if duplicates:
                self.issues.append(f"Duplicate person names found: {[(r['name'], r['count']) for r in duplicates]}")
            else:
                print("   ✓ No obvious duplicate entities")


def main():
    """Run schema validation"""
    
    # Load config
    try:
        with open("config/config.json") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Initialize validator
    validator = Neo4jSchemaValidator(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['user'],
        password=config['neo4j']['password']
    )
    
    try:
        # Run validation
        is_valid, issues, recommendations = validator.validate()
        
        # Exit code
        exit(0 if is_valid else 1)
        
    finally:
        validator.close()


if __name__ == "__main__":
    main()

