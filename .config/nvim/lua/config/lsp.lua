return {
  servers = {
    pylsp = {
      settings = {
        pylsp = {
          plugins = {
            autopep8 = {
              enabled = true, -- Enable autopep8
              ignore = { "E203" }, -- Disable the leading comma rule (E203)
            },
            pycodestyle = {
              ignore = { "E501" },
            },
          },
        },
      },
    },
  },
}
