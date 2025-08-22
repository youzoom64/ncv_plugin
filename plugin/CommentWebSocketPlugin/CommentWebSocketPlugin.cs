using System;
using System.IO;
using System.Text;
using System.Net.WebSockets;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Diagnostics;
using Plugin;
using NicoLibrary;

public class CommentWebSocketPlugin : IPlugin
{
    public string Description => "コメント送信";
    public string Version => "1.0";
    public string Name => "CommentWebSocket";
    public IPluginHost Host { get; set; }
    public bool IsAutoRun => true;

    private HashSet<string> processedComments = new HashSet<string>();
    private HttpListener httpListener;
    private List<WebSocket> clients = new List<WebSocket>();
    private bool isRunning = false;

    public void AutoRun() { Run(); }

    public void Run()
    {
        Host.ReceivedComment += OnCommentReceived;
        StartWebSocket();
        StartPython();
    }

    private async void StartWebSocket()
    {
        try
        {
            httpListener = new HttpListener();
            httpListener.Prefixes.Add("http://localhost:8765/");
            httpListener.Start();
            isRunning = true;

            while (isRunning)
            {
                var context = await httpListener.GetContextAsync();
                if (context.Request.IsWebSocketRequest)
                {
                    ProcessWebSocketRequest(context);
                }
                else
                {
                    context.Response.StatusCode = 400;
                    context.Response.Close();
                }
            }
        }
        catch { }
    }

    private async void ProcessWebSocketRequest(HttpListenerContext context)
    {
        try
        {
            var webSocketContext = await context.AcceptWebSocketAsync(null);
            var webSocket = webSocketContext.WebSocket;

            lock (clients) { clients.Add(webSocket); }

            var buffer = new byte[4096];
            while (webSocket.State == WebSocketState.Open)
            {
                try
                {
                    var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

                    if (result.MessageType == WebSocketMessageType.Text && result.Count > 0)
                    {
                        string receivedMessage = Encoding.UTF8.GetString(buffer, 0, result.Count);

                        // デバッグ用
                        File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                            $"{DateTime.Now}: 受信メッセージ = {receivedMessage}\n");

                        // JSON解析（send_commentコマンドのみ対応）
                        if (receivedMessage.Contains("\"action\": \"send_comment\"") && receivedMessage.Contains("\"message\":"))
                        {
                            File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                $"{DateTime.Now}: send_commentアクション検出\n");

                            // より正確なJSON解析
                            int actionStart = receivedMessage.IndexOf("\"action\": \"send_comment\"");
                            int messageStart = receivedMessage.IndexOf("\"message\": \"") + 12;

                            File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                $"{DateTime.Now}: actionStart={actionStart}, messageStart={messageStart}\n");

                            if (actionStart >= 0 && messageStart > 11)
                            {
                                File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                    $"{DateTime.Now}: 解析開始\n");

                                // シンプルな方法で試す
                                int messageEnd = receivedMessage.IndexOf("\"}", messageStart);
                                if (messageEnd == -1) messageEnd = receivedMessage.LastIndexOf("\"");

                                File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                    $"{DateTime.Now}: messageEnd={messageEnd}\n");

                                if (messageEnd > messageStart)
                                {
                                    string message = receivedMessage.Substring(messageStart, messageEnd - messageStart);

                                    File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                        $"{DateTime.Now}: 抽出されたメッセージ(エスケープ前) = {message}\n");

                                    // Unicodeエスケープを解除
                                    message = System.Text.RegularExpressions.Regex.Unescape(message);

                                    File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                        $"{DateTime.Now}: 送信するコメント = {message}\n");

                                    // NCVでコメント送信
                                    bool result_send = Host.SendComment(message);

                                    File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                        $"{DateTime.Now}: 送信結果 = {result_send}\n");
                                }
                                else
                                {
                                    File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                        $"{DateTime.Now}: messageEnd <= messageStart エラー\n");
                                }
                            }
                            else
                            {
                                File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                    $"{DateTime.Now}: actionStart または messageStart が無効\n");
                            }
                        }
                        else
                        {
                            File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                                $"{DateTime.Now}: send_commentアクション未検出\n");
                        }
                    }
                }
                catch (Exception ex)
                {
                    File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                        $"{DateTime.Now}: 受信エラー = {ex.Message}\n");
                    break;
                }
            }

            lock (clients) { clients.Remove(webSocket); }
        }
        catch (Exception ex)
        {
            File.AppendAllText(@"F:\project_root\app_workspaces\niconico\debug_received.log",
                $"{DateTime.Now}: WebSocket処理エラー = {ex.Message}\n");
        }
    }
    private void StartPython()
    {
        try
        {
            var process = new Process();
            process.StartInfo.FileName = @"C:\project_root\app_workspaces\niconico\start_voice_system.bat";
            process.StartInfo.CreateNoWindow = false;
            process.StartInfo.UseShellExecute = true;
            process.Start();
        }
        catch { }
    }

    private void OnCommentReceived(object sender, ReceivedCommentEventArgs e)
    {
        try
        {
            int count = e.CommentDataList.Count;
            if (count == 0) return;

            NicoLibrary.NicoLiveData.LiveCommentData commentData = e.CommentDataList[count - 1];

            string commentKey = $"{commentData.Comment}_{commentData.UserId}";
            if (processedComments.Contains(commentKey)) return;
            processedComments.Add(commentKey);

            // JSONエスケープ処理を追加
            string escapedComment = EscapeJsonString(commentData.Comment ?? "");
            string escapedUserId = EscapeJsonString(commentData.UserId ?? "");
            string escapedMail = EscapeJsonString(commentData.Mail ?? "");

            string json = $"{{" +
                $"\"comment\":\"{escapedComment}\"," +
                $"\"user_id\":\"{escapedUserId}\"," +
                $"\"mail\":\"{escapedMail}\"," +
                $"\"comment_no\":{commentData.No}," +
                $"\"premium\":{commentData.Premium}," +
                $"\"date\":\"{commentData.Date}\"," +
                $"\"timestamp\":\"{DateTime.Now}\"" +
                $"}}";

            byte[] bytes = Encoding.UTF8.GetBytes(json);

            lock (clients)
            {
                foreach (var client in clients)
                {
                    if (client.State == WebSocketState.Open)
                        client.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
                }
            }

            if (processedComments.Count > 1000) processedComments.Clear();
        }
        catch { }
    }

    // JSONエスケープ用のヘルパーメソッドを追加
    private string EscapeJsonString(string input)
    {
        if (string.IsNullOrEmpty(input))
            return "";

        return input
            .Replace("\\", "\\\\")  // バックスラッシュ
            .Replace("\"", "\\\"")  // 引用符
            .Replace("\n", "\\n")   // 改行
            .Replace("\r", "\\r")   // キャリッジリターン
            .Replace("\t", "\\t");  // タブ
    }

    public void Dispose()
    {
        isRunning = false;
        httpListener?.Stop();
        if (Host != null) Host.ReceivedComment -= OnCommentReceived;
    }
}