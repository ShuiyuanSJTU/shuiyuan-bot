from fluent_discourse import Discourse, RateLimitError
import requests

class BotAPI:
    def __init__(self, base_url: str, username: str, api_key:str, raise_for_rate_limit: bool = True):
        # Discourse API could not handle non-ascii characters in the username
        # so we will not send the username in the header if it is not ascii
        # This works fine when the api is for single user
        try:
            encoded_username = username.encode("latin-1")
        except UnicodeEncodeError:
            encoded_username = None
        self.client: Discourse = Discourse(
            base_url=base_url, username=encoded_username, api_key=api_key, raise_for_rate_limit=raise_for_rate_limit)
        self.base_url = base_url
        self.username = username

    def get_topic_by_id(self, topic_id) -> dict:
        return self.client.t[topic_id].json.get()

    def get_post_by_id(self, post_id) -> dict:
        return self.client.posts[post_id].json.get()

    def get_post_replies_by_id(self, post_id) -> dict:
        return self.client.posts[post_id].replies.json.get()

    def create_private_message(self, title, raw, target_usernames, **kwargs):
        if isinstance(target_usernames, str):
            target_usernames = target_usernames.split(',')
        topic_data = {
            "title": title,
            "raw": raw,
            "archetype": "private_message",
            "target_recipients": ','.join(target_usernames),
        }
        kwargs.update(topic_data)
        return self.create_post_raw(kwargs)

    def create_post(self, raw, topic_id, reply_to_post_number=None, **kwargs):
        post_data = {
            "raw": raw,
            "topic_id": topic_id,
        }
        if reply_to_post_number is not None:
            post_data["reply_to_post_number"] = reply_to_post_number
        kwargs.update(post_data)
        return self.create_post_raw(kwargs)

    def create_topic(self, title, raw, category, tags, **kwargs):
        topic_data = {
            "title": title,
            "raw": raw,
            "category": category,
            "tags": tags,
        }
        kwargs.update(topic_data)
        return self.create_post_raw(kwargs)

    def create_post_raw(self, data):
        return self.client.posts.json.post(data=data)

    def close_topic(self, topic_id, close=True, until=None):
        return self.update_topic_status(topic_id, 'closed', close, until)

    def update_topic_status(self, topic_id, status, enabled, until=None):
        data = {
            'status': status,
        }
        if enabled is True:
            data['enabled'] = 'true'
        elif enabled is False:
            data['enabled'] = 'false'
        else:
            data['enabled'] = enabled
        if until is not None:
            data['until'] = until
        return self.client.t[topic_id].status.put(data)

    def update_post_wiki(self, post_id, wiki=True):
        return self.client.posts[post_id].wiki.put(data={'wiki': wiki})

    def update_post_owner(self, topic_id, post_ids, username, **kwargs):
        if isinstance(post_ids, int):
            post_ids = [post_ids]
        data = {'post_ids': post_ids, 'username': username}
        data.update(kwargs)
        return self.client.t[topic_id]['change-owner'].post(data)

    def close_topic_and_create_new(self, old_topic_id, title=None, raw=None, **kwargs):
        old_topic = self.get_topic_by_id(old_topic_id)
        tags = old_topic.get('tags', [])
        category = old_topic.get('category_id')
        if title is None:
            title = old_topic.get('title')
        if raw is None:
            raw = old_topic.get('title')
        self.close_topic(old_topic_id)
        new_topic = self.create_topic(title, raw, category, tags, **kwargs)
        new_post_id = new_topic.get('id')
        new_topic_id = new_topic.get('topic_id')
        self.update_post_wiki(new_post_id, True)
        return new_topic

    def create_upload(self, file, file_name):
        url = self.client.uploads.json._make_url()
        headers = self.client._headers.copy()
        del headers['Content-Type']
        files = {
            'files[]': (file_name, file)
        }
        params = {
            'type': 'composer',
            'name': '123.txt'
        }
        r = requests.post(url, files=files, headers=headers, params=params)
        if r.status_code == 200:
            try:
                return r.json()
            except requests.JSONDecodeError as e:
                # Request succeeded but response body was not valid JSON
                return r.text
        elif r.status_code == 429:
            raise RateLimitError("Rate limit hit")
        else:
            return self.client._handle_error(r, 'post', url, None, None)
