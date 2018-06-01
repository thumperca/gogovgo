import React, { Component } from "react";

import Header from "../Header";
import Footer from "../Footer";

class LogIn extends Component {
    render() {
        return (
            <div id="signup" className="login">
                <Header />
                <div className="body">
                    <h3 className="text-center">Sign In</h3>
                    <div className="form-group email">
                        <input type="email" placeholder="Email address" className="form-control" />
                    </div>
                    <div className="form-group">
                        <input type="password" placeholder="Password" className="form-control" />
                        <p>
                            <u>Forgot password</u>
                        </p>
                    </div>
                    <div className="form-group text-center">
                        <button>SIGN IN</button>
                    </div>
                    <div className="form-group text-center border">
                        <h4>Do not have an account?</h4>
                        <a href="/signup">
                            <u>Sign up - 100% free</u>
                        </a>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }
}

export default LogIn;
