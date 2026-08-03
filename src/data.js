// Mock seed data for the prototype UI.
// Replace this with API responses from the backend once the data service is ready.
export const INITIAL_HISTORY = [
  { id: 1, connector: "Infor Sales", mapper: "Sales Schema Mapper", rules: "Infor Sales Rules", outputs: ["Vector Database", "PostgreSQL", "Kafka"] },
  { id: 2, connector: "Jira Support", mapper: "Standard Field Mapper", rules: "L3 Ticket Rules", outputs: ["MongoDB", "Kafka"] },
  { id: 3, connector: "SharePoint KB", mapper: "Custom JSON Mapper", rules: "Knowledge Base Rules", outputs: ["Vector Database"] },
  { id: 4, connector: "Infor Sales", mapper: "Sales Schema Mapper", rules: "Infor Sales Rules", outputs: ["PostgreSQL", "MongoDB"] },
  { id: 5, connector: "Jira Support", mapper: "Standard Field Mapper", rules: "L3 Ticket Rules", outputs: ["Kafka"] },
  { id: 6, connector: "SharePoint KB", mapper: "Custom JSON Mapper", rules: "Knowledge Base Rules", outputs: ["Vector Database", "MongoDB"] },
];

// Mock configuration values used to populate the form options.
// Replace this with backend-driven configuration data in the future.
export const INITIAL_CONFIG = {
  connectors: ["Infor Sales", "Jira Support", "SharePoint KB"],
  rules: ["Infor Sales Rules", "L3 Ticket Rules", "Knowledge Base Rules"],
  outputs: ["PostgreSQL", "MongoDB", "Kafka", "Vector Database"],
};

export const CONNECTOR_OPTIONS = ["Infor Sales", "Jira Support", "SharePoint KB"];
export const MAPPER_OPTIONS = ["Standard Field Mapper", "Sales Schema Mapper", "Custom JSON Mapper"];
export const RULES_OPTIONS = ["Infor Sales Rules", "L3 Ticket Rules", "Knowledge Base Rules"];
export const OUTPUT_OPTIONS = ["PostgreSQL", "MongoDB", "Kafka", "Vector Database"];
