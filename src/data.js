export const INITIAL_HISTORY = [
  { id: 1, connector: "INFOR Connector", mapper: "Sales Schema Mapper", rules: "Infor Sales Rules", outputs: ["Vector DB", "JSON", "Document DB", "Kafka"] },
  { id: 2, connector: "Salesforce Connector", mapper: "Standard Field Mapper", rules: "Deduplication Rules", outputs: ["JSON", "Kafka"] },
  { id: 3, connector: "SAP Connector", mapper: "Custom JSON Mapper", rules: "Validation Rules", outputs: ["Document DB"] },
  { id: 4, connector: "Postgres Connector", mapper: "Standard Field Mapper", rules: "Infor Sales Rules", outputs: ["Vector DB", "JSON"] },
  { id: 5, connector: "INFOR Connector", mapper: "Sales Schema Mapper", rules: "Deduplication Rules", outputs: ["Kafka"] },
  { id: 6, connector: "Salesforce Connector", mapper: "Custom JSON Mapper", rules: "Validation Rules", outputs: ["Vector DB", "Document DB"] },
  { id: 7, connector: "SAP Connector", mapper: "Standard Field Mapper", rules: "Infor Sales Rules", outputs: ["JSON"] },
  { id: 8, connector: "Postgres Connector", mapper: "Sales Schema Mapper", rules: "Validation Rules", outputs: ["Kafka", "Document DB", "Vector DB"] },
];

export const INITIAL_CONFIG = {
  connectors: ["Connector Entry 1", "Connector Entry 2", "Connector Entry 3", "Connector Entry 4", "Connector Entry 5", "Connector Entry 6"],
  rules: ["Rules Entry 1", "Rules Entry 2", "Rules Entry 3", "Rules Entry 4", "Rules Entry 5", "Rules Entry 6"],
  outputs: ["Output Target Entry 1", "Output Target Entry 2", "Output Target Entry 3", "Output Target Entry 4", "Output Target Entry 5", "Output Target Entry 6"],
};

export const CONNECTOR_OPTIONS = ["INFOR Connector", "Salesforce Connector", "SAP Connector", "Postgres Connector"];
export const MAPPER_OPTIONS = ["Standard Field Mapper", "Sales Schema Mapper", "Custom JSON Mapper"];
export const RULES_OPTIONS = ["Infor Sales Rules", "Deduplication Rules", "Validation Rules"];
export const OUTPUT_OPTIONS = ["Vector DB", "JSON", "Document DB", "Kafka"];
