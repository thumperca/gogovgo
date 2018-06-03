import React, { Component } from "react";
import { gql, graphql } from "react-apollo";

import Header from "../Header";
import Footer from "../Footer";

class SignUp extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = {
            states: [],
            form: { name: "", username: "", email: "", password: "", country: "", zipcode: "" },
            created: false,
            errors: []
        };
    }

    componentDidMount() {
        fetch("/api/countries/")
            .then(res => res.json())
            .then(data => this.setState({ states: data.countries }));
    }

    handleChange(field, event) {
        let form = { ...this.state.form };
        form[field] = event.target.value;
        this.setState({ form: form });
    }

    /**
     * Handle submission
     */
    handleSubmit = () => {
        window.scrollTo(0, 0);
        this.setState({ errors: [], created: false });
        this.props
            .mutate({ variables: { ...this.state.form } })
            .then(({ data: { signup } }) => {
                let state = { busy: false };
                if (signup.created) {
                    state.created = true;
                    state.form = {
                        name: "",
                        email: "",
                        username: "",
                        password: "",
                        country: "",
                        zipcode: ""
                    };
                } else {
                    state.errors = signup.errors;
                }
                this.setState(state);
            })
            .catch(error => {
                console.warn("there was an error sending the query", error);
                this.setState({ errors: [error.graphQLErrors[0].message] });
            });
    };

    /**
     * Alert to show on page
     * @returns JSX
     */
    getAlert() {
        const { errors } = this.state;
        if (errors.length)
            return (
                <div className="alert alert-danger">
                    <strong>Failed!</strong> The following error(s) have occured:
                    <ul>{errors.map((error, index) => <li key={index}>{error}</li>)}</ul>
                </div>
            );
    }

    render() {
        const { form } = this.state;
        let zcode;
        if (form.country === "United States of America") {
            zcode = (
                <div className="form-group">
                    <label>Zip code</label>
                    <input
                        type="text"
                        placeholder="Insert Zip code"
                        className="form-control"
                        onChange={e => this.handleChange("zipcode", e)}
                        value={form.zipcode}
                    />
                </div>
            );
        }
        return (
            <div id="signup">
                <Header />
                <div className="body">
                    <h3 className="text-center">Sign Up</h3>

                    {this.getAlert()}

                    <div className="form-group">
                        <label>Name</label>
                        <p>Your name will be kept private, and NOT published online.</p>
                        <input
                            type="text"
                            placeholder="Insert your name"
                            className="form-control"
                            onChange={e => this.handleChange("name", e)}
                            value={form.name}
                        />
                    </div>
                    <div className="form-group">
                        <label>Username</label>
                        <p>Your username is public, and WILL be published online.</p>
                        <input
                            type="text"
                            placeholder="Insert your username"
                            className="form-control"
                            onChange={e => this.handleChange("username", e)}
                            value={form.username}
                        />
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input
                            type="email"
                            placeholder="Insert your email"
                            className="form-control"
                            onChange={e => this.handleChange("email", e)}
                            value={form.email}
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            placeholder="Insert your password"
                            className="form-control"
                            onChange={e => this.handleChange("password", e)}
                            value={form.password}
                        />
                    </div>
                    <div className="form-group">
                        <label>Select your country</label>
                        <select
                            className="form-control"
                            onChange={e => this.handleChange("country", e)}
                            value={form.country}
                        >
                            <option value="">Select your country</option>
                            <option>United States of America</option>
                            {this.state.states.map((state, index) => {
                                return <option key={index}>{state.long}</option>;
                            })}
                        </select>
                    </div>
                    {zcode}
                    <div className="form-group text-center">
                        <button onClick={this.handleSubmit}>SIGN UP - 100% FREE</button>
                        <p className="terms">
                            By creating an account, you agree to the <u>terms of participation</u>
                            and <u>privacy policy</u>
                        </p>
                    </div>
                    <div className="form-group text-center border">
                        <h4>Already have an account?</h4>
                        <a href="/login">
                            <u>Sign in</u>
                        </a>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }
}

//  GraphQL mutation
const submitQuery = gql`
    mutation(
        $name: String!
        $username: String!
        $email: String!
        $password: String!
        $country: String!
        $zipcode: String!
    ) {
        signup(
            name: $name
            email: $email
            username: $username
            password: $password
            country: $country
            zipcode: $zipcode
        ) {
            created
            errors
        }
    }
`;

export default graphql(submitQuery)(SignUp);
