class CommentDisplay {
  constructor() {
    this.container = document.getElementById("comment-container");
    this.comments = [];
    this.maxComments = 20; // 最大表示コメント数
    this.autoScrollTimer = null;
    this.autoScrollInterval = 20000; // 20秒

    this.init();
  }

  init() {
    this.connectWebSocket();
    this.startAutoScroll();
    this.loadSkinImages();
  }

  // WebSocket接続
  connectWebSocket() {
    try {
      this.ws = new WebSocket("ws://localhost:8080/ws");

      this.ws.onopen = () => {
        console.log("WebSocket接続完了");
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "comment") {
            this.addComment(data);
          }
        } catch (e) {
          console.error("WebSocketデータ解析エラー:", e);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocketエラー:", error);
      };

      this.ws.onclose = () => {
        console.log("WebSocket接続終了");
        // 再接続を試行
        setTimeout(() => this.connectWebSocket(), 5000);
      };
    } catch (e) {
      console.error("WebSocket接続エラー:", e);
    }
  }

  // スキン画像読み込み
  loadSkinImages() {
    this.skinImages = {};
    // スキン画像のプリロード（必要に応じて）
    console.log("スキン画像読み込み完了");
  }

  // コメント追加
  addComment(data) {
    console.log("コメント追加:", data); // デバッグログ追加

    const comment = {
      id: Date.now() + Math.random(),
      text: data.text || "",
      skin: data.skin || null,
      font: data.font || 0,
      timestamp: Date.now(),
    };

    console.log("処理後のコメント:", comment); // デバッグログ追加

    // コメントリストに追加
    this.comments.push(comment);

    // 最大表示数を超えたら古いコメントを削除
    if (this.comments.length > this.maxComments) {
      this.comments.shift();
    }

    // 既存コメントを上に移動
    this.moveAllCommentsUp();

    // 新しいコメントを表示
    this.displayComment(comment);

    // コメントリストを更新
    this.updateCommentPositions();
  }

  // コメント表示
  displayComment(comment) {
    console.log("スキン・フォント適用詳細:", {
      skin: comment.skin,
      font: comment.font,
      text: comment.text,
    });

    const commentElement = document.createElement("div");
    commentElement.className = "comment-item";
    commentElement.id = `comment-${comment.id}`;
    commentElement.style.bottom = "0px";

    // スキン背景設定
    let skinPath;
    if (comment.skin) {
      skinPath = `/skin/${comment.skin}.png`;
      console.log(`カスタムスキン使用: ${skinPath}`);
    } else {
      skinPath = `/skin/6.png`;
      console.log(`デフォルトスキン使用: ${skinPath}`);
    }

    const skinBg = document.createElement("div");
    skinBg.className = "skin-bg";
    skinBg.style.backgroundImage = `url('${skinPath}')`;

    // スキン読み込み確認
    const testImg = new Image();
    testImg.onload = () => {
      console.log(`✅ スキン読み込み成功: ${skinPath}`);
    };
    testImg.onerror = () => {
      console.error(`❌ スキン読み込み失敗: ${skinPath}`);
      // フォールバックスキンを試行
      skinBg.style.backgroundImage = `url('/skin/6.png')`;
    };
    testImg.src = skinPath;

    commentElement.appendChild(skinBg);

    // コメントテキスト
    const fontClass = `font-${comment.font || 0}`;
    const textElement = document.createElement("div");
    textElement.className = `comment-text ${fontClass}`;
    textElement.textContent = comment.text;
    console.log(`フォントクラス適用: ${fontClass}`);

    // フォント適用確認
    const computedStyle = window.getComputedStyle(textElement);
    console.log(`実際のフォント: ${computedStyle.fontFamily}`);

    commentElement.appendChild(textElement);

    // コンテナに追加
    this.container.appendChild(commentElement);

    // アニメーション開始
    requestAnimationFrame(() => {
      commentElement.classList.add("slide-in");
    });

    // アニメーション完了後にクラスを削除
    setTimeout(() => {
      commentElement.classList.remove("slide-in");
    }, 500);
  }

  // 全コメントを上に移動
  moveAllCommentsUp() {
    const commentElements = document.querySelectorAll(".comment-item");
    commentElements.forEach((element) => {
      element.classList.add("moving-up");
      const currentBottom = parseFloat(element.style.bottom) || 0;
      element.style.bottom = currentBottom + 32 + "px";
    });
  }

  // コメント位置を更新
  updateCommentPositions() {
    // 画面外に出たコメントを削除
    const commentElements = document.querySelectorAll(".comment-item");
    commentElements.forEach((element) => {
      const bottom = parseFloat(element.style.bottom) || 0;
      if (bottom > window.innerHeight) {
        element.remove();
      }
    });
  }

  // 自動スクロール開始
  startAutoScroll() {
    this.autoScrollTimer = setInterval(() => {
      this.moveAllCommentsUp();
      this.updateCommentPositions();
    }, this.autoScrollInterval);
  }

  // 自動スクロール停止
  stopAutoScroll() {
    if (this.autoScrollTimer) {
      clearInterval(this.autoScrollTimer);
      this.autoScrollTimer = null;
    }
  }

  // クリーンアップ
  destroy() {
    this.stopAutoScroll();
    if (this.ws) {
      this.ws.close();
    }
  }
}

// ページ読み込み完了後に初期化
document.addEventListener("DOMContentLoaded", () => {
  window.commentDisplay = new CommentDisplay();
});

// ページ離脱時のクリーンアップ
window.addEventListener("beforeunload", () => {
  if (window.commentDisplay) {
    window.commentDisplay.destroy();
  }
});

// エラーハンドリング
window.addEventListener("error", (event) => {
  console.error("JavaScriptエラー:", event.error);
});

// 未処理のPromise拒否
window.addEventListener("unhandledrejection", (event) => {
  console.error("未処理のPromise拒否:", event.reason);
});
