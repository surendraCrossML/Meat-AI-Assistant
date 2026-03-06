import axios from "axios";

export const documentQueryTool = {
    name: "document_query",
    description: "Search internal documents using natural language and return an AI-generated answer.",
    inputSchema: {
        type: "object",
        properties: {
            query: {
                type: "string",
                description: "Natural language question about documents",
            },
        },
        required: ["query"],
    },
};

export async function handleDocumentQuery(args) {
    const query = args.query;

    // Use environment variable or fallback to localhost
    const apiUrl = process.env.DOC_API_URL || "http://127.0.0.1:8000";

    if (!query) {
        throw new Error("Query parameter is required");
    }

    try {
        const response = await axios.post(`${apiUrl}/document/query`, {
            query: query,
        });

        const data = response.data;

        // Extract answer and matching documents
        const answer = data.agent_response || "No answer generated.";
        const matchingDocuments = data.matching_documents || [];

        // Get document names as used by the API
        const documentsUsed = matchingDocuments.map(
            (doc) => doc.document_name || doc.name || doc.title || "Unknown Document"
        );
        const documentCount = matchingDocuments.length;

        // Return the simplified, agent-friendly JSON structure
        const result = {
            answer: answer,
            documents_used: documentsUsed,
            document_count: documentCount,
        };

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(result, null, 2),
                },
            ],
        };
    } catch (error) {
        console.error("Error calling FastAPI backend:", error.message);

        let errorMessage = "Failed to process query.";
        if (error.response) {
            errorMessage = `Backend API error: ${error.response.status} - ${JSON.stringify(error.response.data)}`;
        } else if (error.request) {
            errorMessage = "No response received from Backend API.";
        } else {
            errorMessage = error.message;
        }

        return {
            isError: true,
            content: [
                {
                    type: "text",
                    text: `Error: ${errorMessage}`,
                },
            ],
        };
    }
}
