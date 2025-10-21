return {
    "rmagatti/auto-session",
        config = function()
            local auto_session = require("auto-session")

            auto_session.setup({
              enabled = true,
              auto_create = false,
              show_auto_restore_notif = true,
              auto_restore_last_session = true,
              auto_session_suppress_dirs = { "~/",  "~/Downloads", "~/Documents"},
            })

    local keymap = vim.keymap
        keymap.set("n", "<leader>wr", "<cmd>AutoSession restore<CR>", { desc = "Restore session for cwd" }) 
        keymap.set("n", "<leader>ws", "<cmd>AutoSession save<CR>", { desc = "Save session for auto session root dir" }) 
  end,
}
