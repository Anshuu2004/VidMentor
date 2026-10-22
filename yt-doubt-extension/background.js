const BACKEND_URL = "https://vidmentor-6ixd.onrender.com";

const indexTasks = new Map();

async function parseResponse(res) {
  try {
    const data = await res.json();
    if (!res.ok) {
      return {
        success: false,
        error: data?.error || data?.detail || `Server error (${res.status})`,
      };
    }
    return data;
  } catch (err) {
    return {
      success: false,
      error: `Server returned invalid response (status ${res.status})`,
    };
  }
}

function indexVideo(videoId) {
  if (!videoId) {
    return Promise.resolve({ success: false, error: "Missing video_id" });
  }

  if (indexTasks.has(videoId)) {
    return indexTasks.get(videoId);
  }

  const promise = fetch(`${BACKEND_URL}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId }),
  })
    .then(parseResponse)
    .catch((err) => ({ success: false, error: String(err) }));

  indexTasks.set(videoId, promise);
  return promise;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CHAT") {
    (async () => {
      try {
        if (message.video_id && indexTasks.has(message.video_id)) {
          const indexResult = await indexTasks.get(message.video_id);
          if (!indexResult.success) {
            indexTasks.delete(message.video_id);
            sendResponse({ success: false, error: indexResult.error });
            return;
          }
        }

        const res = await fetch(`${BACKEND_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_id: message.video_id,
            query: message.query,
            current_time: message.current_time,
          }),
        });
        const data = await parseResponse(res);
        sendResponse(data);
      } catch (err) {
        sendResponse({ success: false, error: String(err) });
      }
    })();

    return true; // keeps sendResponse alive for async fetch
  }

  if (message.type === "INDEX") {
    indexVideo(message.video_id)
      .then((data) => sendResponse(data))
      .catch((err) => sendResponse({ success: false, error: String(err) }));

    return true;
  }
});