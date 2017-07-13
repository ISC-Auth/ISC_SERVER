        $.validator.setDefaults({
            highlight: function (element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
            },
            success: function (element) {
                element.closest('.form-group').removeClass('has-error').addClass('has-success');
            },
            errorElement: "span",
            errorPlacement: function (error, element) {
                if (element.is(":radio") || element.is(":checkbox")) {
                    error.appendTo(element.parent().parent().parent());
                } else {
                    error.appendTo(element.parent());
                }
            },
            errorClass: "help-block m-b-none",
            validClass: "help-block m-b-none"


        });

        //以下为官方示例
        $().ready(function () {
            // validate the comment form when it is submitted
            $("#commentForm").validate();

            // validate signup form on keyup and submit
            var icon = "<i class='fa fa-times-circle'></i> ";
            $("#register_form").validate({
                rules: {
                    account_name: {
                        required: true,
                        minlength: 2
                    },
                    password1: {
                        required: true,
                        minlength: 6
                    },
                    password2: {
                        required: true,
                        minlength: 6,
                        equalTo: "#password"
                    },
                    email: {
                        required: true,
                        email: true
                    },
                    account_phone:{
                        required: true,
                        digits:true,
                        rangelength:[11,11]
                    },
                    topic: {
                        required: "#newsletter:checked",
                        minlength: 2
                    },
                    agree: "required"
                },
                messages: {
                    account_name: {
                        required: icon + "请输入您的用户名",
                        minlength: icon + "用户名必须两个字符以上"
                    },
                    password1: {
                        required: icon + "请输入您的密码",
                        minlength: icon + "密码必须6个字符以上"
                    },
                    password2: {
                        required: icon + "请再次输入密码",
                        minlength: icon + "密码必须6个字符以上",
                        equalTo: icon + "两次输入的密码不一致"
                    },
                    email: icon + "请输入您的E-mail",
                    account_phone: {
                        required: icon + "请输入您的手机号码",
                        rangelength: icon + "请输入正确的手机号码",
                    },
                    agree: {
                        required: icon + "必须同意协议后才能注册",
                        element: '#agree-error'
                    }
                }
            });        
            
        });
