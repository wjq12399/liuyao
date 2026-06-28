const https = require("https");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const { question, prompt } = JSON.parse(event.body);
  const DS_KEY = process.env.DEEPSEEK_API_KEY;

  if (!DS_KEY) {
    return { statusCode: 500, body: JSON.stringify({ error: "API Key not configured" }) };
  }

  const sysPrompt = `你是一位精通六爻的卦师。根据卦象数据直接回答用户的问题。
1. 先重复用户的问题
2. 根据本卦和变卦，给出针对该问题的直接回答
3. 引用卦中关键信号（动爻、世爻、六亲）解释为什么
4. 最后给简短建议
5. 语言简洁有温度，控制在 250 字以内`;

  const userMsg = `我的问题：${question}\n\n${prompt}`;

  const reqBody = JSON.stringify({
    model: "deepseek-chat",
    messages: [
      { role: "system", content: sysPrompt },
      { role: "user", content: userMsg }
    ],
    max_tokens: 800,
    temperature: 0.7,
  });

  try {
    const result = await new Promise((resolve, reject) => {
      const req = https.request(
        {
          hostname: "api.deepseek.com",
          path: "/v1/chat/completions",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${DS_KEY}`,
          },
        },
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => resolve(JSON.parse(data)));
        }
      );
      req.on("error", reject);
      req.write(reqBody);
      req.end();
    });

    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify({ result: result.choices[0].message.content }),
    };
  } catch (e) {
    return {
      statusCode: 500,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify({ error: e.message }),
    };
  }
};
